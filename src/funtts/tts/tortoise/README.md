# Tortoise TTS 引擎

Tortoise TTS是一个专注于高质量语音合成的深度学习模型，以其接近真人的语音质量和优秀的语音克隆能力而著称。虽然生成速度较慢，但音质极佳，特别适合需要高质量语音输出的专业应用。

## 🌟 主要特性

- **极高音质**: 接近真人水平的语音质量
- **语音克隆**: 优秀的语音克隆和模仿能力
- **多质量预设**: 从快速到超高质量的多种预设
- **内置语音库**: 12种高质量的预设语音角色
- **情感控制**: 支持不同情感和语调的表达
- **长文本支持**: 适合生成较长的语音内容

## 📦 安装

```bash
# 安装Tortoise TTS依赖
pip install funtts-plus[tortoise]

# 或者单独安装
pip install tortoise-tts>=2.4.0 torch torchaudio soundfile numpy
```

## 🚀 快速开始

### 基础用法

```python
from funtts.tts.tortoise import TortoiseTTS

# 初始化Tortoise TTS引擎
tts = TortoiseTTS()

# 创建TTS请求
from funtts.models import TTSRequest

request = TTSRequest(
    text="Hello, this is Tortoise TTS speaking with incredible quality!",
    voice_name="angie",  # 使用预设语音
    output_dir="./output",
)

# 执行语音合成
response = tts.synthesize(request)
print(f"音频文件: {response.audio_file}")
print(f"音频时长: {response.duration:.2f}秒")
```

### 质量预设选择

Tortoise TTS提供多种质量预设，平衡质量和速度：

```python
# 快速模式（较低质量，快速生成）
tts_fast = TortoiseTTS(preset="fast")

# 标准模式（平衡质量和速度）
tts_standard = TortoiseTTS(preset="standard")

# 高质量模式（高质量，较慢）
tts_high = TortoiseTTS(preset="high_quality")

# 超高质量模式（极高质量，很慢）
tts_ultra = TortoiseTTS(preset="ultra_fast")
```

### 语音克隆

Tortoise TTS的强项是语音克隆，可以学习并模仿特定的声音：

```python
# 使用参考音频进行语音克隆
response = tts.clone_voice(
    text="This voice has been cloned from the reference audio.",
    voice_samples=["reference1.wav", "reference2.wav", "reference3.wav"],
    output_path="./output/cloned_voice.wav",
)

# 单个参考音频克隆
response = tts.clone_voice(
    text="Hello, this is a cloned voice!",
    voice_samples=["single_reference.wav"],
    output_path="./output/single_clone.wav",
)
```

## 🎭 内置语音角色

Tortoise TTS提供了12种高质量的预设语音：

### 女性语音
- `angie` - 温暖友好的女声，适合叙述和对话
- `deniro` - 成熟优雅的女声，适合专业内容
- `emma` - 年轻活泼的女声，适合轻松内容
- `grace` - 温柔舒缓的女声，适合冥想和放松内容
- `halle` - 清晰专业的女声，适合新闻和教育
- `jlaw` - 自信有力的女声，适合演讲和宣传

### 男性语音
- `freeman` - 深沉权威的男声，适合纪录片和严肃内容
- `geralt` - 低沉磁性的男声，适合故事叙述
- `mol` - 温和亲切的男声，适合日常对话
- `pat` - 清晰标准的男声，适合教学和解说
- `snakes` - 独特个性的男声，适合创意内容
- `tom` - 年轻活力的男声，适合娱乐内容

```python
# 获取所有可用语音
voices = tts.list_voices()
for voice in voices:
    print(f"{voice.name}: {voice.description}")

# 使用特定语音
request = TTSRequest(
    text="This is Freeman's voice, deep and authoritative.",
    voice_name="freeman",
    output_dir="./output",
)
response = tts.synthesize(request)
```

## ⚙️ 高级配置

### 自定义参数

```python
# 使用自定义参数初始化
tts = TortoiseTTS(
    preset="high_quality",
    device="cuda",  # 使用GPU加速
    temperature=0.8,  # 控制随机性
    length_penalty=1.0,  # 长度惩罚
    repetition_penalty=2.0,  # 重复惩罚
    top_k=50,  # Top-k采样
    top_p=0.8,  # Top-p采样
)
```

### 设备配置

```python
# 自动选择最佳设备
tts = TortoiseTTS(device="auto")

# 强制使用CPU（较慢但兼容性好）
tts = TortoiseTTS(device="cpu")

# 使用GPU加速（推荐）
tts = TortoiseTTS(device="cuda")

# 使用Apple Silicon的MPS
tts = TortoiseTTS(device="mps")
```

### 质量与速度平衡

```python
# 极速模式 - 最快但质量较低
tts_fastest = TortoiseTTS(preset="ultra_fast", temperature=1.0)

# 平衡模式 - 质量和速度的良好平衡
tts_balanced = TortoiseTTS(preset="standard", temperature=0.8)

# 专业模式 - 最高质量但最慢
tts_professional = TortoiseTTS(
    preset="high_quality", temperature=0.6, repetition_penalty=2.5
)
```

## 🎯 语音克隆详解

### 准备参考音频

```python
# 语音克隆的最佳实践
def prepare_reference_audio():
    """
    参考音频的要求：
    1. 时长：每个文件3-10秒
    2. 质量：清晰，无背景噪音
    3. 数量：2-5个不同的音频文件
    4. 内容：不同的句子或短语
    5. 格式：WAV格式，22050Hz采样率
    """
    pass


# 高质量语音克隆
response = tts.clone_voice(
    text="This is a demonstration of high-quality voice cloning.",
    voice_samples=[
        "reference_1.wav",  # 3-5秒的清晰语音
        "reference_2.wav",  # 不同内容的语音
        "reference_3.wav",  # 再一个不同的语音样本
    ],
    output_path="./output/cloned_professional.wav",
    preset="high_quality",  # 使用高质量预设
)
```

### 批量语音克隆

```python
# 为多个文本使用同一个克隆语音
texts = [
    "Welcome to our service.",
    "Thank you for choosing us.",
    "Have a wonderful day!",
]

reference_samples = ["voice_ref1.wav", "voice_ref2.wav"]

for i, text in enumerate(texts):
    response = tts.clone_voice(
        text=text,
        voice_samples=reference_samples,
        output_path=f"./output/cloned_{i}.wav",
    )
    print(f"Generated: {response}")
```

## 📊 性能优化

### 内存管理

```python
# 对于长文本，建议分段处理
def synthesize_long_text(tts, long_text, max_length=200):
    """
    将长文本分段处理以避免内存问题
    """
    import re

    # 按句子分割
    sentences = re.split(r"[.!?]+", long_text)
    audio_files = []

    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(current_chunk + sentence) < max_length:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                # 处理当前块
                request = TTSRequest(text=current_chunk.strip(), voice_name="angie")
                response = tts.synthesize(request)
                audio_files.append(response.audio_file)

            current_chunk = sentence + ". "

    # 处理最后一块
    if current_chunk:
        request = TTSRequest(text=current_chunk.strip(), voice_name="angie")
        response = tts.synthesize(request)
        audio_files.append(response.audio_file)

    return audio_files
```

### 缓存机制

```python
# 启用缓存以避免重复生成相同内容
import hashlib
import os


class CachedTortoiseTTS:
    def __init__(self, cache_dir="./tts_cache"):
        self.tts = TortoiseTTS()
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def synthesize_cached(self, text, voice_name="angie"):
        # 生成缓存键
        cache_key = hashlib.md5(f"{text}_{voice_name}".encode()).hexdigest()

        cache_file = os.path.join(self.cache_dir, f"{cache_key}.wav")

        if os.path.exists(cache_file):
            print(f"使用缓存: {cache_file}")
            return cache_file

        # 生成新的语音
        request = TTSRequest(
            text=text, voice_name=voice_name, output_dir=self.cache_dir
        )
        response = self.tts.synthesize(request)

        # 重命名为缓存文件
        os.rename(response.audio_file, cache_file)
        return cache_file
```

## 🔧 故障排除

### 常见问题

1. **内存不足错误**
   ```python
   # 使用CPU模式减少GPU内存占用
   tts = TortoiseTTS(device="cpu")
   
   # 或者使用更快的预设
   tts = TortoiseTTS(preset="fast")
   ```

2. **生成速度太慢**
   ```python
   # 使用快速预设
   tts = TortoiseTTS(preset="ultra_fast")

   # 调整参数加快生成
   tts = TortoiseTTS(preset="fast", temperature=1.0, top_k=50)
   ```

3. **语音质量问题**
   ```python
   # 使用高质量预设
   tts = TortoiseTTS(preset="high_quality")

   # 调整温度参数
   tts = TortoiseTTS(
       preset="standard",
       temperature=0.6,  # 降低随机性
       repetition_penalty=2.0,
   )
   ```

### 语音克隆问题

1. **克隆效果不佳**
   - 确保参考音频质量高、清晰无噪音
   - 使用2-5个不同的参考音频文件
   - 参考音频时长控制在3-10秒
   - 使用高质量预设进行克隆

2. **参考音频格式问题**
   ```python
   # 转换音频格式和采样率
   import librosa
   import soundfile as sf


   def prepare_reference_audio(input_file, output_file):
       # 加载音频并转换为22050Hz
       audio, sr = librosa.load(input_file, sr=22050)
       # 保存为WAV格式
       sf.write(output_file, audio, 22050)
   ```

## 📝 注意事项

1. **生成时间**: Tortoise TTS生成速度较慢，特别是高质量模式
2. **内存需求**: 需要较多内存，建议至少8GB RAM
3. **首次运行**: 会自动下载模型文件，需要网络连接
4. **语音克隆**: 需要高质量的参考音频才能获得好的克隆效果
5. **设备选择**: 强烈推荐使用GPU加速

## 🎯 最佳实践

1. **选择合适的预设**: 根据需求平衡质量和速度
2. **准备高质量参考音频**: 语音克隆的关键
3. **分段处理长文本**: 避免内存问题
4. **使用缓存**: 避免重复生成相同内容
5. **GPU加速**: 有条件时优先使用GPU

## 📚 更多示例

查看 `examples/` 目录中的更多使用示例：
- `tortoise_basic.py` - 基础用法示例
- `tortoise_cloning.py` - 语音克隆示例
- `tortoise_quality.py` - 质量对比示例
- `tortoise_batch.py` - 批量处理示例

## 🔗 相关资源

- [Tortoise TTS 官方仓库](https://github.com/neonbjb/tortoise-tts)
- [模型和预训练权重](https://huggingface.co/jbetker/tortoise-tts-v2)
- [语音克隆最佳实践指南](https://github.com/neonbjb/tortoise-tts/wiki)
