#!/usr/bin/env python3
"""
FunTTS基本使用示例
演示如何使用统一接口切换不同的TTS引擎
"""

import os

from funtts import TTSFactory, create_tts, get_available_engines


def main():
    """主函数"""
    print("=== FunTTS 基本使用示例 ===\n")

    # 1. 查看可用的TTS引擎
    print("1. 可用的TTS引擎:")
    engines = get_available_engines()
    for engine in engines:
        print(f"   - {engine}")
    print()

    # 2. 使用默认配置创建TTS实例
    print("2. 使用默认配置创建TTS实例:")
    try:
        tts = create_tts()
        print(f"   成功创建TTS实例: {tts.__class__.__name__}")
        print(f"   引擎信息: {tts.get_engine_info()}")
    except Exception as e:
        print(f"   创建失败: {e}")
    print()

    # 3. 指定引擎创建TTS实例
    test_text = "你好，这是一个TTS测试。"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    for engine_name in engines:
        print(f"3. 测试 {engine_name} 引擎:")
        try:
            # 根据不同引擎选择合适的语音
            voice_name = get_default_voice_for_engine(engine_name)

            # 创建TTS实例
            tts = TTSFactory.create_tts(engine_name, voice_name)

            # 生成音频文件
            audio_file = os.path.join(output_dir, f"test_{engine_name}.wav")

            print(f"   正在生成音频: {audio_file}")
            response = tts.synthesize_text(
                text=test_text,
                voice_name=voice_name,
                output_file=audio_file,
                voice_rate=1.0,
                generate_subtitles=engine_name in ["edge", "azure"],
            )

            if response.success and os.path.exists(audio_file):
                file_size = os.path.getsize(audio_file)
                print(f"   ✓ 音频生成成功，文件大小: {file_size} bytes")
                print(f"   ✓ 音频时长: {response.duration:.2f} 秒")

                if response.subtitle_file and os.path.exists(response.subtitle_file):
                    print(f"   ✓ 字幕文件生成成功: {response.subtitle_file}")
            else:
                print(f"   ✗ 音频生成失败: {response.error_message}")

        except Exception as e:
            print(f"   ✗ 测试失败: {e}")
        print()

    # 4. 获取语音列表示例
    print("4. 获取可用语音列表示例:")
    for engine_name in engines[:2]:  # 只测试前两个引擎
        try:
            tts = TTSFactory.create_tts(engine_name, "default")
            voices = tts.list_voices()
            print(f"   {engine_name} 引擎可用语音数量: {len(voices)}")
            if voices:
                print(f"   示例语音: {voices[0]}")
        except Exception as e:
            print(f"   获取 {engine_name} 语音列表失败: {e}")
    print()

    print("=== 测试完成 ===")


def get_default_voice_for_engine(engine_name: str) -> str:
    """为不同引擎获取默认语音"""
    voice_map = {
        "edge": "zh-CN-XiaoxiaoNeural",
        "azure": "zh-CN-XiaoxiaoNeural",
        "espeak": "zh",
        "pyttsx3": "0",  # 使用第一个可用语音
    }
    return voice_map.get(engine_name, "default")


if __name__ == "__main__":
    main()
