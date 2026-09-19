"""
FarTTS工具函数使用示例
演示音频合并、字幕合并、响应合并等功能
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fartts import TTSRequest, create_tts
from fartts.utils import merge_audio_files, merge_tts_responses


def demo_basic_merge():
    """演示基本的音频和字幕合并"""
    print("=== 基本合并演示 ===")

    # 创建TTS实例
    tts = create_tts("edge")

    # 准备多段文本
    texts = [
        "欢迎使用FarTTS文本转语音系统。",
        "这是一个功能强大的TTS工具库。",
        "支持多种开源TTS引擎和字幕格式。",
    ]

    voices = ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-XiaoyiNeural"]

    # 生成多个TTS响应
    responses = []
    for i, (text, voice) in enumerate(zip(texts, voices)):
        print(f"正在合成第{i + 1}段: {text[:20]}...")

        request = TTSRequest(
            text=text,
            voice_name=voice,
            output_file=f"temp_audio_{i + 1}.wav",
            generate_subtitles=True,
            subtitle_format="srt",
        )

        response = tts.synthesize(request)
        if response.success:
            responses.append(response)
            print(f"  ✓ 合成成功: {response.audio_file}")
        else:
            print(f"  ✗ 合成失败: {response.error_message}")

    if not responses:
        print("没有成功的响应，无法进行合并")
        return

    # 合并响应
    print(f"\n正在合并{len(responses)}个响应...")
    merged_response = merge_tts_responses(
        responses=responses,
        output_audio_file="merged_output.wav",
        gap_duration=0.8,
        subtitle_format="srt",
    )

    if merged_response.success:
        print("✓ 合并成功！")
        print(f"  音频文件: {merged_response.audio_file}")
        print(f"  SRT字幕: {merged_response.subtitle_file}")
        print(f"  FRT字幕: {merged_response.frt_subtitle_file}")
        print(f"  总时长: {merged_response.duration:.2f}秒")
        print(f"  处理时间: {merged_response.processing_time:.2f}秒")
    else:
        print(f"✗ 合并失败: {merged_response.error_message}")


def demo_speaker_merge():
    """演示带说话者信息的合并"""
    print("\n=== 多说话者合并演示 ===")

    # 创建TTS实例
    tts = create_tts("edge")

    # 对话内容
    dialogue = [
        ("小明", "你好，今天天气真不错！", "zh-CN-YunxiNeural"),
        ("小红", "是啊，我们去公园走走吧。", "zh-CN-XiaoxiaoNeural"),
        ("小明", "好主意，我们现在就出发。", "zh-CN-YunxiNeural"),
        ("小红", "太好了，我已经准备好了。", "zh-CN-XiaoxiaoNeural"),
    ]

    # 生成对话音频
    responses = []
    speaker_names = []

    for i, (speaker, text, voice) in enumerate(dialogue):
        print(f"正在合成 {speaker}: {text}")

        request = TTSRequest(
            text=text,
            voice_name=voice,
            output_file=f"dialogue_{i + 1}.wav",
            generate_subtitles=True,
            subtitle_format="srt",
        )

        response = tts.synthesize(request)
        if response.success:
            responses.append(response)
            speaker_names.append(speaker)
            print("  ✓ 合成成功")
        else:
            print(f"  ✗ 合成失败: {response.error_message}")

    if not responses:
        print("没有成功的响应，无法进行合并")
        return

    # 使用带说话者信息的合并
    from fartts.utils.response_utils import merge_tts_responses_with_speakers

    print(f"\n正在合并对话，说话者: {speaker_names}")
    merged_response = merge_tts_responses_with_speakers(
        responses=responses,
        speaker_names=speaker_names,
        output_audio_file="dialogue_merged.wav",
        gap_duration=0.5,
        subtitle_format="srt",
    )

    if merged_response.success:
        print("✓ 对话合并成功！")
        print(f"  音频文件: {merged_response.audio_file}")
        print(f"  字幕文件: {merged_response.subtitle_file}")
        print(f"  FRT字幕: {merged_response.frt_subtitle_file}")

        # 显示字幕内容
        if merged_response.subtitle_maker:
            print("\n字幕内容预览:")
            for segment in merged_response.subtitle_maker.segments[:3]:  # 只显示前3个
                print(
                    f"  {segment.start_time:.1f}s-{segment.end_time:.1f}s [{segment.speaker_name}]: {segment.text}"
                )
    else:
        print(f"✗ 对话合并失败: {merged_response.error_message}")


def demo_audio_only_merge():
    """演示纯音频文件合并"""
    print("\n=== 纯音频合并演示 ===")

    # 假设我们有一些音频文件
    audio_files = ["temp_audio_1.wav", "temp_audio_2.wav", "temp_audio_3.wav"]

    # 检查文件是否存在
    existing_files = [f for f in audio_files if os.path.exists(f)]

    if not existing_files:
        print("没有找到音频文件，跳过纯音频合并演示")
        return

    print(f"找到{len(existing_files)}个音频文件")

    # 合并音频文件
    success = merge_audio_files(
        audio_files=existing_files,
        output_file="audio_only_merged.wav",
        silence_duration=1.0,  # 1秒间隔
    )

    if success:
        print("✓ 纯音频合并成功: audio_only_merged.wav")
    else:
        print("✗ 纯音频合并失败")


def demo_subtitle_operations():
    """演示字幕操作"""
    print("\n=== 字幕操作演示 ===")

    from fartts.models import SubtitleMaker
    from fartts.utils.subtitle_utils import (
        adjust_subtitle_timing,
        merge_subtitle_makers,
        split_subtitle_maker_by_speaker,
    )

    # 创建示例字幕
    subtitle1 = SubtitleMaker()
    subtitle1.add_segment(0.0, 2.0, "第一段字幕", speaker_name="说话者A")
    subtitle1.add_segment(2.0, 4.0, "第二段字幕", speaker_name="说话者A")

    subtitle2 = SubtitleMaker()
    subtitle2.add_segment(0.0, 1.5, "第三段字幕", speaker_name="说话者B")
    subtitle2.add_segment(1.5, 3.0, "第四段字幕", speaker_name="说话者B")

    # 合并字幕
    merged_subtitle = merge_subtitle_makers([subtitle1, subtitle2], gap_duration=0.5)
    print(f"合并后字幕片段数: {len(merged_subtitle.segments)}")

    # 按说话者拆分
    speakers = split_subtitle_maker_by_speaker(merged_subtitle)
    print(f"拆分后说话者数: {len(speakers)}")
    for speaker_id, maker in speakers.items():
        print(f"  {speaker_id}: {len(maker.segments)}个片段")

    # 调整时间
    adjusted_subtitle = adjust_subtitle_timing(
        merged_subtitle,
        time_offset=2.0,  # 延迟2秒
        speed_factor=1.2,  # 加速20%
    )
    print(f"时间调整后总时长: {adjusted_subtitle.get_total_duration():.2f}秒")


def cleanup_temp_files():
    """清理临时文件"""
    print("\n=== 清理临时文件 ===")

    temp_patterns = [
        "temp_audio_*.wav",
        "dialogue_*.wav",
        "*.sub.srt",
        "*.sub.frt",
        "merged_output.wav",
        "dialogue_merged.wav",
        "audio_only_merged.wav",
    ]

    import glob

    for pattern in temp_patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
                print(f"删除: {file}")
            except Exception as e:
                print(f"删除失败 {file}: {e}")


def main():
    """主函数"""
    print("FarTTS工具函数演示")
    print("=" * 50)

    try:
        # 演示基本合并
        demo_basic_merge()

        # 演示多说话者合并
        demo_speaker_merge()

        # 演示纯音频合并
        demo_audio_only_merge()

        # 演示字幕操作
        demo_subtitle_operations()

    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n演示过程中出错: {e}")
    finally:
        # 清理临时文件
        cleanup_temp_files()

    print("\n演示完成！")


if __name__ == "__main__":
    main()
