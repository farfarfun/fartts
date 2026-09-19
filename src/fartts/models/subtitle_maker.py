"""
字幕制作器
支持SRT、VTT、FRT三种格式的字幕生成和解析
"""

from __future__ import annotations

import json
import os
import re
from datetime import timedelta

from .audio_segment import AudioSegment


class SubtitleMaker:
    """字幕制作器，替代edge-tts的SubMaker"""

    def __init__(self, segments: list[AudioSegment] | None = None):
        self.segments = list(segments or [])
        self._total_duration = max(
            (segment.end_time for segment in self.segments), default=0.0
        )

    def add_segment(self, start_time: float, end_time: float, text: str):
        """添加音频片段

        Args:
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            text: 对应文本
        """
        segment = AudioSegment(start_time, end_time, text)
        self.segments.append(segment)
        self._total_duration = max(self._total_duration, end_time)

    def add_segment_from_offset(self, offset: tuple[float, float], text: str):
        """从偏移量添加片段（兼容edge-tts格式）

        Args:
            offset: (开始时间, 持续时间) 元组，时间单位为100纳秒
            text: 对应文本
        """
        start_time = offset[0] / 10000000  # 转换为秒
        duration = offset[1] / 10000000  # 转换为秒
        end_time = start_time + duration
        self.add_segment(start_time, end_time, text)

    def get_total_duration(self) -> float:
        """获取总时长（秒）"""
        return self._total_duration

    def get_segments(self) -> list[AudioSegment]:
        """获取所有音频片段"""
        return self.segments.copy()

    def to_srt(self) -> str:
        """生成SRT格式字幕"""
        srt_content = []

        for i, segment in enumerate(self.segments, 1):
            start_time = self._format_time(segment.start_time)
            end_time = self._format_time(segment.end_time)

            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")

            # 如果有说话者信息，添加到字幕中
            text = segment.text
            if segment.speaker_name or segment.speaker_id:
                speaker = segment.get_display_speaker()
                text = f"[{speaker}] {text}"

            srt_content.append(text)
            srt_content.append("")  # 空行分隔

        return "\n".join(srt_content)

    def to_vtt(self) -> str:
        """生成WebVTT格式字幕"""
        vtt_content = ["WEBVTT", ""]

        for segment in self.segments:
            start_time = self._format_time(segment.start_time, use_comma=False)
            end_time = self._format_time(segment.end_time, use_comma=False)

            vtt_content.append(f"{start_time} --> {end_time}")

            # 如果有说话者信息，添加到字幕中
            text = segment.text
            if segment.speaker_name or segment.speaker_id:
                speaker = segment.get_display_speaker()
                text = f"<v {speaker}>{text}"  # VTT格式的说话者标记

            vtt_content.append(text)
            vtt_content.append("")

        return "\n".join(vtt_content)

    def to_frt(self) -> str:
        """生成FRT格式字幕（FarTTS完整格式，JSON）"""
        data = {
            "format": "FRT",
            "version": "1.0",
            "total_duration": self._total_duration,
            "segments": [segment.to_dict() for segment in self.segments],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _format_time(self, seconds: float, use_comma: bool = True) -> str:
        """格式化时间为字幕格式

        Args:
            seconds: 秒数
            use_comma: 是否使用逗号分隔毫秒（SRT格式）

        Returns:
            格式化的时间字符串
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        millisecs = int((td.total_seconds() % 1) * 1000)

        separator = "," if use_comma else "."
        return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millisecs:03d}"

    def save_to_file(self, file_path: str, format_type: str = "srt"):
        """保存字幕到文件，支持SRT、VTT、FRT格式

        Args:
            file_path: 文件路径
            format_type: 字幕格式，支持 "srt"、"vtt"、"frt"
        """
        format_type = format_type.lower()

        if format_type == "srt":
            content = self.to_srt()
        elif format_type == "vtt":
            content = self.to_vtt()
        elif format_type == "frt":
            content = self.to_frt()
        else:
            raise ValueError(f"不支持的字幕格式: {format_type}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def save_srt(self, file_path: str):
        """保存为SRT格式。"""
        self.save_to_file(file_path, "srt")

    def save_frt(self, file_path: str):
        """保存为FRT格式。"""
        self.save_to_file(file_path, "frt")

    def load_from_file(self, file_path: str) -> bool:
        """从文件加载字幕，支持SRT、VTT、FRT格式

        Args:
            file_path: 字幕文件路径

        Returns:
            bool: 是否加载成功
        """
        try:
            if not os.path.exists(file_path):
                return False

            with open(file_path, encoding="utf-8") as f:
                content = f.read().strip()

            # 清空现有片段
            self.clear()

            # 根据文件扩展名或内容判断格式
            if file_path.lower().endswith(".frt"):
                return self._parse_frt(content)
            elif file_path.lower().endswith(".vtt") or content.startswith("WEBVTT"):
                return self._parse_vtt(content)
            else:
                return self._parse_srt(content)

        except Exception as e:
            print(f"加载字幕文件失败: {e}")
            return False

    def clear(self):
        """清空所有片段"""
        self.segments.clear()
        self._total_duration = 0.0

    def get_speakers(self) -> list[str]:
        """获取所有说话者列表"""
        speakers = set()
        for segment in self.segments:
            if segment.speaker_id:
                speakers.add(segment.speaker_id)
            elif segment.speaker_name:
                speakers.add(segment.speaker_name)
        return list(speakers)

    def get_segments_by_speaker(self, speaker_id: str) -> list[AudioSegment]:
        """获取指定说话者的所有片段"""
        return [
            segment
            for segment in self.segments
            if segment.speaker_id == speaker_id or segment.speaker_name == speaker_id
        ]

    def get_speaker_duration(self, speaker_id: str) -> float:
        """获取指定说话者的总时长"""
        segments = self.get_segments_by_speaker(speaker_id)
        return sum(segment.duration for segment in segments)

    def __len__(self) -> int:
        """返回片段数量"""
        return len(self.segments)

    def __bool__(self) -> bool:
        """检查是否有片段"""
        return len(self.segments) > 0

    def _parse_srt(self, content: str) -> bool:
        """解析SRT格式字幕"""
        try:
            # SRT格式解析
            blocks = re.split(r"\n\s*\n", content.strip())

            for block in blocks:
                if not block.strip():
                    continue

                lines = block.strip().split("\n")
                if len(lines) < 3:
                    continue

                # 解析时间行
                time_line = lines[1]
                time_match = re.match(
                    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})",
                    time_line,
                )
                if not time_match:
                    continue

                start_time = self._parse_time(time_match.group(1))
                end_time = self._parse_time(time_match.group(2))

                # 解析文本（可能有多行）
                text_lines = lines[2:]
                text = "\n".join(text_lines)

                # 解析说话者信息（如果有）
                speaker_name = None
                if text.startswith("[") and "]" in text:
                    speaker_end = text.find("]")
                    speaker_name = text[1:speaker_end]
                    text = text[speaker_end + 1 :].strip()

                # 添加片段
                segment = AudioSegment(
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    speaker_name=speaker_name,
                )
                self.segments.append(segment)
                self._total_duration = max(self._total_duration, end_time)

            return True

        except Exception as e:
            print(f"解析SRT格式失败: {e}")
            return False

    def _parse_vtt(self, content: str) -> bool:
        """解析WebVTT格式字幕"""
        try:
            lines = content.split("\n")
            i = 0

            # 跳过WEBVTT头部
            while i < len(lines) and not lines[i].strip().startswith("WEBVTT"):
                i += 1
            i += 1

            while i < len(lines):
                line = lines[i].strip()

                # 跳过空行和注释
                if not line or line.startswith("NOTE"):
                    i += 1
                    continue

                # 查找时间行
                time_match = re.match(
                    r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})",
                    line,
                )
                if time_match:
                    start_time = self._parse_time(time_match.group(1))
                    end_time = self._parse_time(time_match.group(2))

                    # 读取文本行
                    i += 1
                    text_lines = []
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1

                    text = "\n".join(text_lines)

                    # 解析说话者信息（VTT格式）
                    speaker_name = None
                    if "<v " in text:
                        speaker_match = re.search(r"<v ([^>]+)>", text)
                        if speaker_match:
                            speaker_name = speaker_match.group(1)
                            text = re.sub(r"<v [^>]+>", "", text).strip()

                    # 添加片段
                    segment = AudioSegment(
                        start_time=start_time,
                        end_time=end_time,
                        text=text,
                        speaker_name=speaker_name,
                    )
                    self.segments.append(segment)
                    self._total_duration = max(self._total_duration, end_time)

                i += 1

            return True

        except Exception as e:
            print(f"解析VTT格式失败: {e}")
            return False

    def _parse_frt(self, content: str) -> bool:
        """解析FRT格式字幕"""
        try:
            data = json.loads(content)

            # 验证格式
            if data.get("format") != "FRT":
                print("不是有效的FRT格式文件")
                return False

            # 恢复总时长
            self._total_duration = data.get("total_duration", 0.0)

            # 恢复所有片段
            for segment_data in data.get("segments", []):
                segment = AudioSegment(
                    start_time=segment_data.get("start_time", 0.0),
                    end_time=segment_data.get("end_time", 0.0),
                    text=segment_data.get("text", ""),
                    speaker_id=segment_data.get("speaker_id"),
                    speaker_name=segment_data.get("speaker_name"),
                    voice_name=segment_data.get("voice_name"),
                    emotion=segment_data.get("emotion"),
                    style=segment_data.get("style"),
                    segment_id=segment_data.get("segment_id"),
                    metadata=segment_data.get("metadata", {}),
                )
                self.segments.append(segment)

            return True

        except Exception as e:
            print(f"解析FRT格式失败: {e}")
            return False

    def _parse_time(self, time_str: str) -> float:
        """解析时间字符串为秒数"""
        # 处理逗号分隔符（SRT格式）
        time_str = time_str.replace(",", ".")

        # 解析时:分:秒.毫秒格式
        parts = time_str.split(":")
        if len(parts) != 3:
            return 0.0

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split(".")
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0

    @staticmethod
    def load_from_file_static(file_path: str) -> SubtitleMaker | None:
        """静态方法：从文件加载字幕，支持SRT、VTT、FRT格式

        Args:
            file_path: 字幕文件路径

        Returns:
            SubtitleMaker对象，加载失败返回None
        """
        try:
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return None

            with open(file_path, encoding="utf-8") as f:
                content = f.read().strip()

            subtitle_maker = SubtitleMaker()

            # 根据文件扩展名或内容判断格式
            if file_path.lower().endswith(".frt"):
                success = subtitle_maker._parse_frt(content)
            elif file_path.lower().endswith(".vtt") or content.startswith("WEBVTT"):
                success = subtitle_maker._parse_vtt(content)
            else:
                success = subtitle_maker._parse_srt(content)

            return subtitle_maker if success else None

        except Exception as e:
            print(f"加载字幕文件失败: {e}")
            return None

    @staticmethod
    def save_to_file_static(
        subtitle_maker: SubtitleMaker, file_path: str, format_type: str = "srt"
    ) -> bool:
        """静态方法：保存字幕到文件，支持SRT、VTT、FRT格式

        Args:
            subtitle_maker: SubtitleMaker对象
            file_path: 文件路径
            format_type: 字幕格式，支持 "srt"、"vtt"、"frt"

        Returns:
            bool: 是否保存成功
        """
        try:
            format_type = format_type.lower()

            if format_type == "srt":
                content = subtitle_maker.to_srt()
            elif format_type == "vtt":
                content = subtitle_maker.to_vtt()
            elif format_type == "frt":
                content = subtitle_maker.to_frt()
            else:
                print(f"不支持的字幕格式: {format_type}")
                return False

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"保存字幕文件失败: {e}")
            return False

    @staticmethod
    def generate_subtitle_filename(audio_file: str, format_type: str = "srt") -> str:
        """根据音频文件名生成字幕文件名

        Args:
            audio_file: 音频文件路径
            format_type: 字幕格式（srt、vtt或frt）

        Returns:
            str: 字幕文件路径
        """
        if not audio_file:
            return f"subtitle.{format_type}"

        # 获取音频文件的目录和基础名称
        audio_dir = os.path.dirname(audio_file)
        audio_basename = os.path.splitext(os.path.basename(audio_file))[0]

        # 生成字幕文件名，使用.sub.后缀来区分
        subtitle_filename = f"{audio_basename}.sub.{format_type}"

        return (
            os.path.join(audio_dir, subtitle_filename)
            if audio_dir
            else subtitle_filename
        )
