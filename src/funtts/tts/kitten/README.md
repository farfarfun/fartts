# KittenTTS引擎

## 概述

KittenTTS是一个基于深度学习的高质量文本转语音引擎，采用先进的神经网络架构，能够生成自然流畅、情感丰富的语音。该引擎支持多种语言和语音风格，适合对语音质量要求较高的应用场景。

## 特性

- ✅ **高质量语音**: 基于深度学习模型，生成自然流畅的语音
- ✅ **多语言支持**: 支持中文、英文等多种语言
- ✅ **语音风格**: 支持不同的语音风格和情感表达
- ✅ **GPU加速**: 支持CUDA加速，提高合成速度
- ✅ **字幕生成**: 支持SRT和FRT格式字幕
- ✅ **参数调节**: 支持语音速度、音调等参数调节
- ✅ **多种格式**: 支持WAV、MP3、OGG等音频格式
- ✅ **批量处理**: 支持批量文本合成

## 依赖要求

### Python包依赖
```bash
# 核心依赖
pip install kitten-tts
pip install torch torchvision torchaudio

# 音频处理依赖
pip install soundfile librosa

# 可选依赖（用于更多音频格式支持）
pip install pydub ffmpeg-python
```

### 系统依赖

#### GPU支持（推荐）
- NVIDIA GPU with CUDA support
- CUDA 11.0+ 
- cuDNN 8.0+

#### CPU支持
- 支持AVX指令集的CPU
- 至少4GB内存（推荐8GB+）

### 模型文件

KittenTTS需要预训练模型文件：

```bash
# 下载预训练模型（示例）
wget https://github.com/KittenML/KittenTTS/releases/download/v1.0/kitten_tts_model.pth
wget https://github.com/KittenML/KittenTTS/releases/download/v1.0/kitten_tts_config.json
```

## 配置说明

KittenTTS引擎支持以下配置参数：

```python
from funtts.tts.kitten import KittenTTS

# 基本配置
tts = KittenTTS(
    voice_name="default",  # 语音名称
    model_path="path/to/model.pth",  # 模型文件路径
    config_path="path/to/config.json",  # 配置文件路径
    device="auto",  # 计算设备 ('cpu', 'cuda', 'auto')
    sample_rate=22050,  # 采样率
    speed=1.0,  # 语音速度倍数
    pitch=1.0,  # 音调调节
)
```

### 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_path` | str | None | 模型文件路径，为空时使用预训练模型 |
| `config_path` | str | None | 配置文件路径，为空时使用默认配置 |
| `device` | str | "auto" | 计算设备，auto自动选择最佳设备 |
| `sample_rate` | int | 22050 | 音频采样率 |
| `speed` | float | 1.0 | 语音速度倍数 |
| `pitch` | float | 1.0 | 音调调节倍数 |

## 使用示例

### 基本使用

```python
from funtts.models import TTSRequest
from funtts.tts.kitten import KittenTTS

# 创建TTS引擎
tts = KittenTTS(
    voice_name="default",
    model_path="models/kitten_tts_model.pth",
    config_path="models/kitten_tts_config.json",
)

# 创建请求
request = TTSRequest(
    text="你好，这是KittenTTS语音合成测试。",
    output_file="output.wav",
    voice_rate=1.0,
    generate_subtitles=True,
)

# 执行合成
response = tts.synthesize(request)

if response.success:
    print(f"合成成功: {response.audio_file}")
    print(f"时长: {response.duration:.2f}秒")
    if response.subtitle_file:
        print(f"字幕文件: {response.subtitle_file}")
else:
    print(f"合成失败: {response.error_message}")
```

### 获取可用语音

```python
# 获取所有可用语音
voices = tts.list_voices()
for voice in voices:
    print(f"语音: {voice.display_name}")
    print(f"语言: {voice.language}")
    print(f"性别: {voice.gender}")
    print(f"风格: {voice.metadata.get('style', 'N/A')}")
    print("---")

# 按语言过滤
chinese_voices = tts.list_voices(language="zh")
english_voices = tts.list_voices(language="en")
```

### 高级配置

```python
# 使用GPU加速
tts = KittenTTS(
    voice_name="zh-female-001",
    device="cuda",
    sample_rate=24000,
    speed=1.2,  # 1.2倍速
    pitch=1.1,  # 稍微提高音调
)

# 检查语音可用性
if tts.is_voice_available("zh-female-001"):
    print("语音可用")
else:
    print("语音不可用")
```

### 批量合成

```python
texts = ["第一段文本内容", "第二段文本内容", "第三段文本内容"]

for i, text in enumerate(texts):
    request = TTSRequest(
        text=text, output_file=f"output_{i + 1}.wav", generate_subtitles=True
    )

    response = tts.synthesize(request)
    if response.success:
        print(f"文件 {i + 1} 合成完成: {response.duration:.2f}s")
    else:
        print(f"文件 {i + 1} 合成失败: {response.error_message}")
```

### 不同音频格式

```python
# WAV格式（默认）
request = TTSRequest(text="测试文本", output_file="output.wav", output_format="wav")

# MP3格式
request = TTSRequest(text="测试文本", output_file="output.mp3", output_format="mp3")

# OGG格式
request = TTSRequest(text="测试文本", output_file="output.ogg", output_format="ogg")
```

## 可用语音

KittenTTS支持的语音取决于加载的模型。常见的语音包括：

### 中文语音
- `zh-female-001`: 中文女声，标准普通话
- `zh-male-001`: 中文男声，标准普通话
- `zh-female-emotion`: 中文女声，情感丰富
- `zh-child`: 中文童声

### 英文语音
- `en-female-001`: 英文女声，美式发音
- `en-male-001`: 英文男声，美式发音
- `en-british-female`: 英文女声，英式发音

### 多语言语音
- `multilingual-female`: 多语言女声
- `multilingual-male`: 多语言男声

> **注意**: 具体可用的语音列表取决于您使用的模型文件。使用 `tts.list_voices()` 查看当前模型支持的所有语音。

## 性能特点

| 特性 | 说明 |
|------|------|
| **质量** | 高质量，接近真人语音 |
| **速度** | GPU: 实时合成，CPU: 较慢 |
| **内存占用** | 中等，模型加载需要1-2GB |
| **文件大小** | 中等，高质量音频文件 |
| **延迟** | 低延迟，适合实时应用 |
| **并发支持** | 支持，但受GPU内存限制 |

## 限制说明

1. **硬件要求**: 推荐使用GPU，CPU合成速度较慢
2. **模型依赖**: 需要下载预训练模型文件
3. **文本长度**: 单次合成建议不超过5000字符
4. **内存占用**: 模型加载需要较多内存
5. **语音数量**: 语音数量取决于模型支持
6. **商业使用**: 请查看KittenTTS的许可证条款

## 故障排除

### 常见问题

#### 1. 模型加载失败
```
错误: KittenTTS模型初始化失败
```
**解决方案**:
- 检查模型文件路径是否正确
- 确认模型文件完整性
- 检查配置文件格式是否正确
- 确保有足够的内存空间

#### 2. CUDA相关错误
```
错误: CUDA out of memory
```
**解决方案**:
- 减少batch size或文本长度
- 使用CPU模式：`device="cpu"`
- 清理GPU内存：重启Python进程
- 升级GPU或增加显存

#### 3. 依赖包问题
```
错误: No module named 'kitten_tts'
```
**解决方案**:
```bash
# 安装KittenTTS
pip install kitten-tts

# 安装PyTorch（根据您的CUDA版本）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装音频处理库
pip install soundfile librosa
```

#### 4. 音频质量问题
```
问题: 合成的语音质量不佳
```
**解决方案**:
- 使用更高的采样率：`sample_rate=24000`
- 检查模型文件是否为最新版本
- 调整语音参数：`speed`, `pitch`
- 确保输入文本格式正确

#### 5. 合成速度慢
```
问题: 语音合成速度很慢
```
**解决方案**:
- 使用GPU加速：`device="cuda"`
- 减少文本长度，分段处理
- 升级硬件配置
- 使用更轻量级的模型

### 调试技巧

1. **启用详细日志**:
```python
from farlog import getLogger

logger = getLogger("funtts", level="DEBUG")
```

2. **检查引擎信息**:
```python
info = tts.get_engine_info()
print(info)
```

3. **测试GPU可用性**:
```python
import torch

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device count: {torch.cuda.device_count()}")
```

4. **监控资源使用**:
```python
# 监控GPU内存
if torch.cuda.is_available():
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
    print(f"GPU memory used: {torch.cuda.memory_allocated() / 1e9:.1f}GB")
```

## 最佳实践

### 1. 模型管理
- 将模型文件放在固定目录
- 定期更新到最新版本
- 备份重要的自定义模型

### 2. 性能优化
- 优先使用GPU进行合成
- 合理设置batch size
- 避免频繁加载/卸载模型

### 3. 文本预处理
- 去除特殊字符和格式
- 适当分段长文本
- 统一标点符号格式

### 4. 质量控制
- 测试不同语音的效果
- 调整合适的语音参数
- 验证输出音频质量

## 版本历史

### v1.0.0
- ✅ 初始版本发布
- ✅ 支持基本语音合成功能
- ✅ 支持GPU/CPU切换
- ✅ 支持多种音频格式
- ✅ 支持字幕生成
- ✅ 完善错误处理和日志记录

## 相关链接

- **官方网站**: [KittenTTS GitHub](https://github.com/KittenML/KittenTTS)
- **KittenTTS文档**: [https://github.com/KittenML/KittenTTS/blob/main/README.md](https://github.com/KittenML/KittenTTS/blob/main/README.md)
- **PyTorch官网**: [https://pytorch.org/](https://pytorch.org/)
- **CUDA工具包**: [https://developer.nvidia.com/cuda-toolkit](https://developer.nvidia.com/cuda-toolkit)
- **模型下载**: [https://github.com/KittenML/KittenTTS/releases](https://github.com/KittenML/KittenTTS/releases)
- **问题反馈**: [https://github.com/KittenML/KittenTTS/issues](https://github.com/KittenML/KittenTTS/issues)
- **社区讨论**: [https://github.com/KittenML/KittenTTS/discussions](https://github.com/KittenML/KittenTTS/discussions)
