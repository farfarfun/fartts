"""
字幕处理工具函数
提供SubtitleMaker合并等功能
"""

from farlog import getLogger

from ..models import AudioSegment, SubtitleMaker

logger = getLogger("fartts")


def merge_subtitle_makers(
    subtitle_makers: list[SubtitleMaker],
    time_offsets: list[float] | None = None,
    gap_duration: float = 0.5,
) -> SubtitleMaker:
    """合并多个SubtitleMaker对象

    Args:
        subtitle_makers: SubtitleMaker对象列表
        time_offsets: 每个字幕的时间偏移列表，如果为None则自动计算
        gap_duration: 字幕间隔时长（秒）

    Returns:
        SubtitleMaker: 合并后的字幕制作器
    """
    if not subtitle_makers:
        logger.warning("没有提供字幕制作器")
        return SubtitleMaker()

    if len(subtitle_makers) == 1:
        logger.info("只有一个字幕制作器，直接返回副本")
        merged = SubtitleMaker()
        merged.segments = subtitle_makers[0].segments.copy()
        merged._total_duration = subtitle_makers[0]._total_duration
        return merged

    try:
        merged = SubtitleMaker()
        current_offset = 0.0

        # 如果没有提供时间偏移，自动计算
        if time_offsets is None:
            time_offsets = [0.0]
            for i, maker in enumerate(subtitle_makers[:-1]):
                current_offset += maker.get_total_duration() + gap_duration
                time_offsets.append(current_offset)

        # 检查偏移列表长度
        if len(time_offsets) != len(subtitle_makers):
            logger.error(
                f"时间偏移列表长度({len(time_offsets)})与字幕制作器数量({len(subtitle_makers)})不匹配"
            )
            time_offsets = time_offsets[: len(subtitle_makers)]
            while len(time_offsets) < len(subtitle_makers):
                time_offsets.append(
                    time_offsets[-1] + gap_duration if time_offsets else 0.0
                )

        # 合并所有片段
        for i, (maker, offset) in enumerate(zip(subtitle_makers, time_offsets)):
            logger.info(f"合并第{i + 1}个字幕制作器，时间偏移: {offset}秒")

            for segment in maker.segments:
                # 创建新的片段，调整时间
                new_segment = AudioSegment(
                    start_time=segment.start_time + offset,
                    end_time=segment.end_time + offset,
                    text=segment.text,
                    speaker_id=segment.speaker_id,
                    speaker_name=segment.speaker_name,
                    voice_name=segment.voice_name,
                    emotion=segment.emotion,
                    style=segment.style,
                    segment_id=f"{i}_{segment.segment_id}"
                    if segment.segment_id
                    else f"{i}_{len(merged.segments)}",
                    metadata=segment.metadata.copy() if segment.metadata else {},
                )

                merged.segments.append(new_segment)

        # 更新总时长
        if merged.segments:
            merged._total_duration = max(seg.end_time for seg in merged.segments)

        logger.success(
            f"字幕合并完成，共{len(merged.segments)}个片段，总时长{merged._total_duration:.2f}秒"
        )
        return merged

    except Exception as e:
        logger.error(f"字幕合并失败: {e}")
        return SubtitleMaker()


def merge_subtitle_makers_with_speakers(
    subtitle_makers: list[SubtitleMaker],
    speaker_names: list[str] | None = None,
    time_offsets: list[float] | None = None,
    gap_duration: float = 0.5,
) -> SubtitleMaker:
    """合并多个SubtitleMaker对象，并设置说话者信息

    Args:
        subtitle_makers: SubtitleMaker对象列表
        speaker_names: 每个字幕对应的说话者名称列表
        time_offsets: 每个字幕的时间偏移列表
        gap_duration: 字幕间隔时长（秒）

    Returns:
        SubtitleMaker: 合并后的字幕制作器
    """
    if not subtitle_makers:
        return SubtitleMaker()

    # 如果没有提供说话者名称，使用默认名称
    if speaker_names is None:
        speaker_names = [f"说话者{i + 1}" for i in range(len(subtitle_makers))]
    elif len(speaker_names) < len(subtitle_makers):
        # 补充缺失的说话者名称
        for i in range(len(speaker_names), len(subtitle_makers)):
            speaker_names.append(f"说话者{i + 1}")

    try:
        # 先合并字幕
        merged = merge_subtitle_makers(subtitle_makers, time_offsets, gap_duration)

        # 更新说话者信息
        segment_index = 0
        for i, maker in enumerate(subtitle_makers):
            speaker_name = speaker_names[i]

            # 为这个制作器的所有片段设置说话者信息
            for _ in range(len(maker.segments)):
                if segment_index < len(merged.segments):
                    merged.segments[segment_index].speaker_name = speaker_name
                    merged.segments[segment_index].speaker_id = f"speaker_{i + 1}"
                    segment_index += 1

        logger.success(f"带说话者信息的字幕合并完成，说话者: {speaker_names}")
        return merged

    except Exception as e:
        logger.error(f"带说话者信息的字幕合并失败: {e}")
        return SubtitleMaker()


def split_subtitle_maker_by_speaker(
    subtitle_maker: SubtitleMaker,
) -> dict[str, SubtitleMaker]:
    """按说话者拆分SubtitleMaker

    Args:
        subtitle_maker: 要拆分的字幕制作器

    Returns:
        dict: 说话者ID到SubtitleMaker的映射
    """
    try:
        speakers = {}

        for segment in subtitle_maker.segments:
            speaker_id = segment.speaker_id or segment.speaker_name or "unknown"

            if speaker_id not in speakers:
                speakers[speaker_id] = SubtitleMaker()

            # 调整时间偏移，使每个说话者的字幕从0开始
            if not speakers[speaker_id].segments:
                time_offset = segment.start_time
            else:
                time_offset = speakers[speaker_id].segments[0].start_time

            new_segment = AudioSegment(
                start_time=segment.start_time - time_offset,
                end_time=segment.end_time - time_offset,
                text=segment.text,
                speaker_id=segment.speaker_id,
                speaker_name=segment.speaker_name,
                voice_name=segment.voice_name,
                emotion=segment.emotion,
                style=segment.style,
                segment_id=segment.segment_id,
                metadata=segment.metadata.copy() if segment.metadata else {},
            )

            speakers[speaker_id].segments.append(new_segment)

        # 更新每个说话者的总时长
        for speaker_id, maker in speakers.items():
            if maker.segments:
                maker._total_duration = max(seg.end_time for seg in maker.segments)

        logger.success(f"字幕按说话者拆分完成，共{len(speakers)}个说话者")
        return speakers

    except Exception as e:
        logger.error(f"字幕拆分失败: {e}")
        return {}


def adjust_subtitle_timing(
    subtitle_maker: SubtitleMaker, time_offset: float = 0.0, speed_factor: float = 1.0
) -> SubtitleMaker:
    """调整字幕时间

    Args:
        subtitle_maker: 字幕制作器
        time_offset: 时间偏移（秒）
        speed_factor: 速度因子（>1加速，<1减速）

    Returns:
        SubtitleMaker: 调整后的字幕制作器
    """
    try:
        adjusted = SubtitleMaker()

        for segment in subtitle_maker.segments:
            new_segment = AudioSegment(
                start_time=(segment.start_time * speed_factor) + time_offset,
                end_time=(segment.end_time * speed_factor) + time_offset,
                text=segment.text,
                speaker_id=segment.speaker_id,
                speaker_name=segment.speaker_name,
                voice_name=segment.voice_name,
                emotion=segment.emotion,
                style=segment.style,
                segment_id=segment.segment_id,
                metadata=segment.metadata.copy() if segment.metadata else {},
            )

            adjusted.segments.append(new_segment)

        # 更新总时长
        if adjusted.segments:
            adjusted._total_duration = max(seg.end_time for seg in adjusted.segments)

        logger.success(f"字幕时间调整完成，偏移{time_offset}秒，速度因子{speed_factor}")
        return adjusted

    except Exception as e:
        logger.error(f"字幕时间调整失败: {e}")
        return SubtitleMaker()
