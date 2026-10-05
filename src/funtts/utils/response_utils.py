"""
TTS响应处理工具函数
提供TTSResponse合并等功能
"""

import os
from typing import Any

from farlog import getLogger

from ..models import TTSResponse
from .audio_utils import get_audio_duration, merge_audio_files
from .subtitle_utils import merge_subtitle_makers

logger = getLogger("funtts")


def merge_tts_responses(
    responses: list[TTSResponse],
    output_audio_file: str,
    gap_duration: float = 0.5,
    subtitle_format: str = "srt",
    cleanup_temp_files: bool = True,
) -> TTSResponse:
    """合并多个TTSResponse对象

    Args:
        responses: TTSResponse对象列表
        output_audio_file: 输出音频文件路径
        gap_duration: 音频间隔时长（秒）
        subtitle_format: 字幕格式 (srt, vtt)
        cleanup_temp_files: 是否清理临时文件

    Returns:
        TTSResponse: 合并后的响应对象
    """
    if not responses:
        logger.error("没有提供响应对象")
        return TTSResponse(success=False, error_message="没有提供响应对象")

    # 检查所有响应是否成功
    failed_responses = [r for r in responses if not r.success]
    if failed_responses:
        logger.error(f"发现{len(failed_responses)}个失败的响应")
        return TTSResponse(
            success=False,
            error_message=f"包含失败的响应: {[r.error_message for r in failed_responses]}",
        )

    # 检查音频文件是否存在
    audio_files = []
    for i, response in enumerate(responses):
        if not response.audio_file or not os.path.exists(response.audio_file):
            logger.error(f"第{i + 1}个响应的音频文件不存在: {response.audio_file}")
            return TTSResponse(
                success=False, error_message=f"音频文件不存在: {response.audio_file}"
            )
        audio_files.append(response.audio_file)

    try:
        # 1. 合并音频文件
        logger.info(f"开始合并{len(audio_files)}个音频文件")
        audio_success = merge_audio_files(
            audio_files=audio_files,
            output_file=output_audio_file,
            silence_duration=gap_duration,
        )

        if not audio_success:
            return TTSResponse(success=False, error_message="音频文件合并失败")

        # 2. 合并字幕
        subtitle_makers = []
        time_offsets = []
        current_offset = 0.0

        for response in responses:
            if response.subtitle_maker:
                subtitle_makers.append(response.subtitle_maker)
                time_offsets.append(current_offset)

                # 计算下一个偏移时间
                duration = response.duration
                if duration <= 0 and response.audio_file:
                    # 尝试从音频文件获取时长
                    duration = get_audio_duration(response.audio_file) or 0.0

                current_offset += duration + gap_duration

        merged_subtitle_maker = None
        if subtitle_makers:
            logger.info(f"开始合并{len(subtitle_makers)}个字幕制作器")
            merged_subtitle_maker = merge_subtitle_makers(
                subtitle_makers=subtitle_makers,
                time_offsets=time_offsets,
                gap_duration=gap_duration,
            )

        # 3. 生成字幕文件
        subtitle_file = None
        frt_subtitle_file = None

        if merged_subtitle_maker:
            # 生成标准格式字幕文件
            subtitle_file = merged_subtitle_maker.generate_subtitle_filename(
                output_audio_file, subtitle_format
            )
            merged_subtitle_maker.save_to_file_static(
                merged_subtitle_maker, subtitle_file, subtitle_format
            )

            # 生成FRT格式字幕文件
            frt_subtitle_file = merged_subtitle_maker.generate_subtitle_filename(
                output_audio_file, "frt"
            )
            merged_subtitle_maker.save_to_file_static(
                merged_subtitle_maker, frt_subtitle_file, "frt"
            )

        # 4. 计算合并后的总时长
        total_duration = get_audio_duration(output_audio_file) or 0.0

        # 5. 合并引擎信息和其他元数据
        engine_info = _merge_engine_info([r.engine_info for r in responses])

        # 6. 创建合并后的响应
        merged_response = TTSResponse(
            success=True,
            audio_file=output_audio_file,
            subtitle_maker=merged_subtitle_maker,
            subtitle_file=subtitle_file,
            frt_subtitle_file=frt_subtitle_file,
            duration=total_duration,
            voice_used=_get_merged_voice_names(responses),
            engine_info=engine_info,
            processing_time=sum(r.processing_time for r in responses),
        )

        # 7. 清理临时文件（可选）
        if cleanup_temp_files:
            _cleanup_temp_files(responses, output_audio_file)

        logger.success(f"TTS响应合并完成: {output_audio_file}")
        return merged_response

    except Exception as e:
        logger.error(f"TTS响应合并失败: {e}")
        return TTSResponse(success=False, error_message=f"合并失败: {str(e)}")


def merge_tts_responses_with_speakers(
    responses: list[TTSResponse],
    speaker_names: list[str],
    output_audio_file: str,
    gap_duration: float = 0.5,
    subtitle_format: str = "srt",
) -> TTSResponse:
    """合并多个TTSResponse对象，并设置说话者信息

    Args:
        responses: TTSResponse对象列表
        speaker_names: 每个响应对应的说话者名称
        output_audio_file: 输出音频文件路径
        gap_duration: 音频间隔时长（秒）
        subtitle_format: 字幕格式

    Returns:
        TTSResponse: 合并后的响应对象
    """
    # 先进行基本合并
    merged_response = merge_tts_responses(
        responses=responses,
        output_audio_file=output_audio_file,
        gap_duration=gap_duration,
        subtitle_format=subtitle_format,
        cleanup_temp_files=False,  # 暂时不清理，后面可能还需要
    )

    if not merged_response.success or not merged_response.subtitle_maker:
        return merged_response

    try:
        # 更新说话者信息
        from .subtitle_utils import merge_subtitle_makers_with_speakers

        subtitle_makers = [r.subtitle_maker for r in responses if r.subtitle_maker]
        if subtitle_makers:
            # 重新合并字幕，这次带说话者信息
            time_offsets = []
            current_offset = 0.0

            for response in responses:
                time_offsets.append(current_offset)
                duration = (
                    response.duration or get_audio_duration(response.audio_file) or 0.0
                )
                current_offset += duration + gap_duration

            merged_subtitle_maker = merge_subtitle_makers_with_speakers(
                subtitle_makers=subtitle_makers,
                speaker_names=speaker_names,
                time_offsets=time_offsets,
                gap_duration=gap_duration,
            )

            # 更新响应中的字幕制作器
            merged_response.subtitle_maker = merged_subtitle_maker

            # 重新生成字幕文件
            if merged_response.subtitle_file:
                merged_subtitle_maker.save_to_file_static(
                    merged_subtitle_maker,
                    merged_response.subtitle_file,
                    subtitle_format,
                )

            if merged_response.frt_subtitle_file:
                merged_subtitle_maker.save_to_file_static(
                    merged_subtitle_maker, merged_response.frt_subtitle_file, "frt"
                )

        logger.success("带说话者信息的TTS响应合并完成")
        return merged_response

    except Exception as e:
        logger.error(f"说话者信息设置失败: {e}")
        return merged_response


def _merge_engine_info(engine_infos: list[dict[str, Any] | None]) -> dict[str, Any]:
    """合并引擎信息"""
    merged = {"merged_from": len(engine_infos), "engines": []}

    for i, info in enumerate(engine_infos):
        if info:
            merged["engines"].append(
                {
                    "index": i,
                    "engine_name": info.get("engine_name", "unknown"),
                    "info": info,
                }
            )

    return merged


def _get_merged_voice_names(responses: list[TTSResponse]) -> str:
    """获取合并后的语音名称"""
    voices = []
    for response in responses:
        if response.voice_used:
            voices.append(response.voice_used)

    if not voices:
        return "unknown"
    elif len(set(voices)) == 1:
        return voices[0]
    else:
        return f"混合语音({len(voices)}个)"


def _cleanup_temp_files(responses: list[TTSResponse], keep_file: str):
    """清理临时文件"""
    try:
        for response in responses:
            # 删除原始音频文件（除了要保留的文件）
            if response.audio_file and response.audio_file != keep_file:
                if os.path.exists(response.audio_file):
                    os.remove(response.audio_file)
                    logger.info(f"清理临时音频文件: {response.audio_file}")

            # 删除原始字幕文件
            if response.subtitle_file and os.path.exists(response.subtitle_file):
                os.remove(response.subtitle_file)
                logger.info(f"清理临时字幕文件: {response.subtitle_file}")

            if response.frt_subtitle_file and os.path.exists(
                response.frt_subtitle_file
            ):
                os.remove(response.frt_subtitle_file)
                logger.info(f"清理临时FRT字幕文件: {response.frt_subtitle_file}")

    except Exception as e:
        logger.warning(f"清理临时文件时出错: {e}")


def create_batch_response(
    responses: list[TTSResponse], batch_info: dict[str, Any] | None = None
) -> TTSResponse:
    """创建批处理响应对象

    Args:
        responses: 响应对象列表
        batch_info: 批处理信息

    Returns:
        TTSResponse: 批处理响应对象
    """
    success_count = sum(1 for r in responses if r.success)
    total_count = len(responses)

    # 收集所有音频文件
    audio_files = [r.audio_file for r in responses if r.success and r.audio_file]

    # 计算总时长和处理时间
    total_duration = sum(r.duration for r in responses if r.success)
    total_processing_time = sum(r.processing_time for r in responses)

    # 创建批处理响应
    batch_response = TTSResponse(
        success=success_count == total_count,
        error_message=f"批处理完成: {success_count}/{total_count} 成功"
        if success_count < total_count
        else "",
        duration=total_duration,
        processing_time=total_processing_time,
        engine_info={
            "batch_mode": True,
            "total_requests": total_count,
            "success_count": success_count,
            "failed_count": total_count - success_count,
            "audio_files": audio_files,
            "batch_info": batch_info or {},
        },
    )

    logger.info(f"批处理响应创建完成: {success_count}/{total_count} 成功")
    return batch_response
