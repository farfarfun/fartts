"""
音频处理工具函数
提供音频文件合并等功能
"""

import os

from farlog import getLogger

logger = getLogger("funtts")


def merge_audio_files(
    audio_files: list[str],
    output_file: str,
    format: str = "wav",
    silence_duration: float = 0.5,
) -> bool:
    """合并多个音频文件

    Args:
        audio_files: 音频文件路径列表
        output_file: 输出文件路径
        format: 输出格式 (wav, mp3, etc.)
        silence_duration: 音频间隔时长（秒）

    Returns:
        bool: 是否合并成功
    """
    try:
        # 检查输入文件
        for audio_file in audio_files:
            if not os.path.exists(audio_file):
                logger.error(f"音频文件不存在: {audio_file}")
                return False

        # 尝试使用pydub进行音频合并
        try:
            from pydub import AudioSegment

            # 加载第一个音频文件
            combined = AudioSegment.from_file(audio_files[0])
            logger.info(f"加载音频文件: {audio_files[0]}")

            # 创建静音片段
            silence = AudioSegment.silent(
                duration=int(silence_duration * 1000)
            )  # 转换为毫秒

            # 依次合并其他音频文件
            for audio_file in audio_files[1:]:
                audio = AudioSegment.from_file(audio_file)
                combined = combined + silence + audio
                logger.info(f"合并音频文件: {audio_file}")

            # 导出合并后的音频
            combined.export(output_file, format=format)
            logger.success(f"音频合并完成: {output_file}")
            return True

        except ImportError:
            logger.warning("pydub未安装，尝试使用ffmpeg")
            return _merge_with_ffmpeg(audio_files, output_file, silence_duration)

    except Exception as e:
        logger.error(f"音频合并失败: {e}")
        return False


def _merge_with_ffmpeg(
    audio_files: list[str], output_file: str, silence_duration: float
) -> bool:
    """使用ffmpeg合并音频文件"""
    try:
        import subprocess

        # 创建临时文件列表
        temp_list_file = "temp_audio_list.txt"

        with open(temp_list_file, "w") as f:
            for i, audio_file in enumerate(audio_files):
                f.write(f"file '{audio_file}'\n")
                if i < len(audio_files) - 1:  # 不在最后一个文件后添加静音
                    # 创建临时静音文件
                    silence_file = f"temp_silence_{i}.wav"
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-f",
                            "lavfi",
                            "-i",
                            f"anullsrc=duration={silence_duration}",
                            "-y",
                            silence_file,
                        ],
                        check=True,
                        capture_output=True,
                    )
                    f.write(f"file '{silence_file}'\n")

        # 使用ffmpeg合并
        cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            temp_list_file,
            "-c",
            "copy",
            "-y",
            output_file,
        ]

        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # 清理临时文件
        os.remove(temp_list_file)
        for i in range(len(audio_files) - 1):
            silence_file = f"temp_silence_{i}.wav"
            if os.path.exists(silence_file):
                os.remove(silence_file)

        logger.success(f"音频合并完成(ffmpeg): {output_file}")
        return True

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"ffmpeg合并失败: {e}")
        return False
    except Exception as e:
        logger.error(f"音频合并失败: {e}")
        return False


def get_audio_duration(audio_file: str) -> float | None:
    """获取音频文件时长

    Args:
        audio_file: 音频文件路径

    Returns:
        float: 音频时长（秒），失败返回None
    """
    try:
        if not os.path.exists(audio_file):
            return None

        # 尝试使用pydub
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_file)
            return len(audio) / 1000.0  # 转换为秒

        except ImportError:
            # 尝试使用ffprobe
            import json
            import subprocess

            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                audio_file,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            return float(data["format"]["duration"])

    except Exception as e:
        logger.error(f"获取音频时长失败: {e}")
        return None


def convert_audio_format(
    input_file: str,
    output_file: str,
    target_format: str = "wav",
    sample_rate: int = 16000,
) -> bool:
    """转换音频格式

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        target_format: 目标格式
        sample_rate: 采样率

    Returns:
        bool: 是否转换成功
    """
    try:
        if not os.path.exists(input_file):
            logger.error(f"输入文件不存在: {input_file}")
            return False

        # 尝试使用pydub
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(input_file)
            audio = audio.set_frame_rate(sample_rate)
            audio.export(output_file, format=target_format)

            logger.success(f"音频格式转换完成: {output_file}")
            return True

        except ImportError:
            # 使用ffmpeg
            import subprocess

            cmd = [
                "ffmpeg",
                "-i",
                input_file,
                "-ar",
                str(sample_rate),
                "-y",
                output_file,
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.success(f"音频格式转换完成(ffmpeg): {output_file}")
            return True

    except Exception as e:
        logger.error(f"音频格式转换失败: {e}")
        return False
