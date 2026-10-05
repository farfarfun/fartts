# Bark TTS 引擎

Bark是由Suno AI开发的基于Transformer的文本转语音模型，以其独特的非语言声音生成能力而闻名。它不仅能生成高质量的语音，还能产生笑声、叹息、背景音乐等特效音效。

## 🌟 主要特性

- **高质量语音合成**: 基于先进的Transformer架构
- **非语言声音**: 支持笑声、叹息、咳嗽等自然声音
- **背景音乐生成**: 可以生成简单的背景音乐
- **多语言支持**: 支持英语、中文、德语、西班牙语、法语等多种语言
- **情感表达**: 能够表达不同的情感和语调
- **特效标记**: 支持特殊标记来控制音效生成

## 📦 安装

```bash
# 安装Bark TTS依赖
pip install funtts-plus[bark]

# 或者单独安装
pip install bark>=0.1.5 torch torchaudio scipy soundfile numpy
```

## 🚀 快速开始

### 基础用法

```python
from funtts.tts.bark import BarkTTS

# 初始化Bark TTS引擎
tts = BarkTTS()

# 创建TTS请求
from funtts.models import TTSRequest

request = TTSRequest(
    text="Hello, this is Bark TTS speaking!",
    voice_name="v2/en_speaker_6",  # 使用预设语音
    output_dir="./output",
)

# 执行语音合成
response = tts.synthesize(request)
print(f"音频文件: {response.audio_file}")
print(f"音频时长: {response.duration:.2f}秒")
```

### 特效语音生成

Bark TTS的独特功能是支持非语言声音和特效：

```python
# 生成带笑声的语音
response = tts.generate_with_effects(
    text="That's really funny!", output_path="./output/funny.wav", effects=["laughter"]
)

# 生成带背景音乐的语音
response = tts.generate_with_effects(
    text="Welcome to our podcast!",
    output_path="./output/podcast_intro.wav",
    effects=["music"],
)

# 生成带掌声的语音
response = tts.generate_with_effects(
    text="Thank you for your attention!",
    output_path="./output/applause.wav",
    effects=["applause"],
)

# 组合多种特效
response = tts.generate_with_effects(
    text="What an amazing performance!",
    output_path="./output/combined.wav",
    effects=["music", "applause", "laughter"],
)
```

### 使用特效标记

你也可以直接在文本中使用特效标记：

```python
# 在文本中直接使用特效标记
text_with_effects = """
Hello everyone! [laughter] 
Welcome to today's show! ♪ This is going to be fun ♪
[applause] Thank you, thank you! [sighs]
"""

request = TTSRequest(
    text=text_with_effects, voice_name="v2/en_speaker_1", output_dir="./output"
)

response = tts.synthesize(request)
```

## 🎭 可用语音

Bark TTS提供了多种预设语音角色：

### 英语语音
- `v2/en_speaker_0` - 男声，清晰专业
- `v2/en_speaker_1` - 女声，温暖友好
- `v2/en_speaker_2` - 男声，深沉权威
- `v2/en_speaker_3` - 女声，年轻活力
- `v2/en_speaker_4` - 男声，随意轻松
- `v2/en_speaker_5` - 女声，成熟优雅
- `v2/en_speaker_6` - 男声，富有表现力（推荐）
- `v2/en_speaker_7` - 女声，温柔舒缓
- `v2/en_speaker_8` - 男声，自信强势
- `v2/en_speaker_9` - 女声，明亮开朗

### 中文语音
- `v2/zh_speaker_0` - 女声，标准普通话
- `v2/zh_speaker_1` - 男声，标准普通话

### 其他语言
- `v2/de_speaker_0` - 德语语音
- `v2/es_speaker_0` - 西班牙语语音
- `v2/fr_speaker_0` - 法语语音

```python
# 获取所有可用语音
voices = tts.list_voices()
for voice in voices:
    print(f"{voice.name}: {voice.description}")

# 按语言筛选
chinese_voices = tts.list_voices(language="zh")
```

## ⚙️ 高级配置

### 自定义参数

```python
# 使用自定义参数初始化
tts = BarkTTS(
    device="cuda",  # 使用GPU加速
    text_temp=0.7,  # 文本生成温度
    waveform_temp=0.7,  # 波形生成温度
    use_small_models=False,  # 使用完整模型获得更好质量
    silent=True,  # 静默模式
)
```

### 设备配置

```python
# 自动选择最佳设备
tts = BarkTTS(device="auto")

# 强制使用CPU
tts = BarkTTS(device="cpu")

# 使用GPU（如果可用）
tts = BarkTTS(device="cuda")

# 使用Apple Silicon的MPS（如果可用）
tts = BarkTTS(device="mps")
```

### 质量与速度平衡

```python
# 高质量模式（较慢）
tts = BarkTTS(use_small_models=False, text_temp=0.6, waveform_temp=0.6)

# 快速模式（质量略低）
tts = BarkTTS(use_small_models=True, text_temp=0.8, waveform_temp=0.8)
```

## 🎵 特效标记参考

Bark支持多种特效标记，可以直接在文本中使用：

### 非语言声音
- `[laughter]` - 笑声
- `[laughs]` - 笑声（变体）
- `[sighs]` - 叹息
- `[music]` - 音乐
- `[gasps]` - 喘息
- `[clears throat]` - 清嗓子
- `[hesitation]` - 犹豫

### 音乐标记
- `♪ 文本 ♪` - 为文本添加音乐背景
- `🎵 文本 🎵` - 音乐标记（变体）

### 情感标记
- `[happy]` - 快乐
- `[sad]` - 悲伤
- `[angry]` - 愤怒
- `[surprised]` - 惊讶

## 📊 性能优化

### 内存管理

```python
# 对于长文本，建议分段处理
def synthesize_long_text(tts, long_text, max_length=100):
    sentences = long_text.split(".")
    audio_files = []

    for sentence in sentences:
        if len(sentence.strip()) > 0:
            request = TTSRequest(
                text=sentence.strip() + ".", voice_name="v2/en_speaker_6"
            )
            response = tts.synthesize(request)
            audio_files.append(response.audio_file)

    return audio_files
```

### 批量处理

```python
# 批量生成多个语音文件
texts = [
    "Hello, this is the first message.",
    "This is the second message with [laughter].",
    "♪ This is a musical message ♪",
]

for i, text in enumerate(texts):
    request = TTSRequest(
        text=text, voice_name="v2/en_speaker_6", output_dir=f"./output/batch_{i}"
    )
    response = tts.synthesize(request)
    print(f"Generated: {response.audio_file}")
```

## 🔧 故障排除

### 常见问题

1. **内存不足错误**
   ```python
   # 使用小模型减少内存占用
   tts = BarkTTS(use_small_models=True)
   ```

2. **CUDA内存错误**
   ```python
   # 强制使用CPU
   tts = BarkTTS(device="cpu")
   ```

3. **音频质量问题**
   ```python
   # 调整温度参数
   tts = BarkTTS(
       text_temp=0.6,  # 降低温度获得更稳定的输出
       waveform_temp=0.6,
   )
   ```

### 依赖问题

如果遇到导入错误，请确保安装了所有必要的依赖：

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install bark>=0.1.5 scipy soundfile numpy
```

## 📝 注意事项

1. **首次运行**: Bark会自动下载模型文件，可能需要几分钟时间
2. **内存需求**: 完整模型需要较多内存，建议至少8GB RAM
3. **生成时间**: 语音生成可能需要几秒到几分钟，取决于文本长度和硬件
4. **特效使用**: 过度使用特效标记可能影响语音质量
5. **语言混合**: 避免在同一段文本中混合多种语言

## 🎯 最佳实践

1. **选择合适的语音**: 根据内容类型选择合适的speaker
2. **控制文本长度**: 单次合成建议不超过200个字符
3. **合理使用特效**: 特效标记要适度，不要过度使用
4. **设备选择**: 有GPU时优先使用GPU加速
5. **批量处理**: 对于大量文本，使用批量处理提高效率

## 📚 更多示例

查看 `examples/` 目录中的更多使用示例：
- `bark_basic.py` - 基础用法示例
- `bark_effects.py` - 特效使用示例
- `bark_multilingual.py` - 多语言示例
- `bark_batch.py` - 批量处理示例
