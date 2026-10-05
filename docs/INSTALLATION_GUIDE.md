# FunTTS 安装和部署指南

本指南将详细介绍如何安装和部署FunTTS项目，包括各种TTS引擎的配置和最佳实践。

## 📋 系统要求

### 基础要求
- **Python**: 3.8+ (推荐3.9+)
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **内存**: 最少4GB RAM (推荐8GB+)
- **存储**: 至少2GB可用空间

### GPU支持（可选）
- **CUDA**: 11.0+ (用于Bark TTS, Tortoise TTS等)
- **显存**: 最少4GB VRAM (推荐8GB+)
- **驱动**: 最新的NVIDIA驱动程序

## 🚀 快速安装

### 1. 基础安装

```bash
# 创建虚拟环境并安装默认的 Edge TTS 引擎
uv venv funtts-env
source funtts-env/bin/activate  # Linux/macOS
# 或 funtts-env\Scripts\activate  # Windows
uv pip install "funtts-plus[edge]"
```

### 2. 验证安装

```python
import funtts

print(f"FunTTS版本: {funtts.__version__}")
print(f"可用引擎: {funtts.get_available_engines()}")
```

## 🎯 按需安装TTS引擎

### Edge TTS (推荐首选)

```bash
# 安装Edge TTS
uv pip install "funtts-plus[edge]"

# 验证安装
python -c "from funtts.tts.edge import EdgeTTS; print('Edge TTS安装成功')"
```

**特点:**
- ✅ 完全免费，无需API密钥
- ✅ 高质量语音，200+种语音
- ✅ 网络连接即可使用
- ✅ 支持100+种语言

### Azure TTS (企业级)

```bash
# 安装Azure TTS
uv pip install "funtts-plus[azure]"

# 设置API密钥
export AZURE_SPEECH_KEY="your-api-key"
export AZURE_SPEECH_REGION="your-region"
```

**配置步骤:**
1. 访问 [Azure Portal](https://portal.azure.com)
2. 创建"语音服务"资源
3. 获取API密钥和区域信息
4. 设置环境变量

**验证:**
```python
from funtts.tts.azure import AzureTTS

tts = AzureTTS()
voices = tts.list_voices()
print(f"可用语音数量: {len(voices)}")
```

### Bark TTS (创意特效)

```bash
# 安装Bark TTS
uv pip install "funtts-plus[bark]"

# 首次运行会自动下载模型（需要网络连接）
python -c "from funtts.tts.bark import BarkTTS; BarkTTS()"
```

**注意事项:**
- 🔥 需要较多内存（推荐8GB+）
- 🌐 首次运行需下载模型文件（约2GB）
- ⚡ 生成速度较慢，但支持特效音效
- 🎮 GPU加速可显著提升速度

### Tortoise TTS (极致质量)

```bash
# 安装Tortoise TTS
uv pip install "funtts-plus[tortoise]"

# 首次运行会下载模型
python -c "from funtts.tts.tortoise import TortoiseTTS; TortoiseTTS()"
```

**注意事项:**
- 🐢 生成速度很慢，但质量极高
- 💾 需要大量存储空间（模型文件约3GB）
- 🔥 强烈推荐使用GPU加速
- 🎯 适合专业语音克隆应用

### IndexTTS2 (情感控制)

```bash
# 安装IndexTTS2
uv pip install "funtts-plus[indextts]"
```

### KittenTTS (神经网络)

```bash
# 安装KittenTTS
uv pip install "funtts-plus[kitten]"
```

### eSpeak (轻量级)

```bash
# 安装eSpeak
uv pip install "funtts-plus[espeak]"

# Linux系统需要额外安装系统包
sudo apt-get install espeak espeak-data  # Ubuntu/Debian
sudo yum install espeak espeak-devel     # CentOS/RHEL
brew install espeak                      # macOS
```

### pyttsx3 (跨平台)

```bash
# 安装pyttsx3
uv pip install "funtts-plus[pyttsx3]"

# 使用系统内置TTS引擎，无需额外配置
```

### 完整安装

```bash
# 安装标准引擎集合（IndexTTS 需单独安装）
uv pip install "funtts-plus[all]"
```

## 🐳 Docker部署

### 基础镜像

```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    espeak espeak-data \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装FunTTS
RUN pip install funtts-plus[edge,azure,espeak,pyttsx3]

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY . .

# 暴露端口（如果需要）
EXPOSE 8000

# 启动命令
CMD ["python", "app.py"]
```

### GPU支持镜像

```dockerfile
FROM nvidia/cuda:11.8-runtime-ubuntu20.04

# 安装Python和依赖
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    espeak espeak-data \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装PyTorch (GPU版本)
RUN pip3 install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装FunTTS (包含GPU支持的引擎)
RUN pip3 install "funtts-plus[bark,tortoise,indextts,kitten]"

WORKDIR /app
COPY . .

CMD ["python3", "app.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  funtts:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AZURE_SPEECH_KEY=${AZURE_SPEECH_KEY}
      - AZURE_SPEECH_REGION=${AZURE_SPEECH_REGION}
    volumes:
      - ./output:/app/output
      - ./cache:/app/cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## 🔧 环境配置

### Azure TTS 环境变量

Azure 凭据只从环境变量读取：

```bash
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=your-azure-region
```

### 配置文件

FunTTS 使用 JSON 配置文件，默认路径为 `~/.funtts/config.json`。例如：

```json
{
  "default_engine": "edge",
  "default_voice": "zh-CN-XiaoxiaoNeural",
  "default_rate": 1.0,
  "engines": {
    "edge": {"enabled": true, "config": {}},
    "azure": {"enabled": true, "config": {"service_region": "eastus"}}
  }
}
```

## 🧪 测试安装

### 基础功能测试

```python
#!/usr/bin/env python3
"""FunTTS安装测试脚本"""

import funtts
from funtts.models import TTSRequest


def test_installation():
    """测试FunTTS安装"""
    print("🧪 开始测试FunTTS安装...")

    # 测试基础导入
    try:
        print(f"✅ FunTTS版本: {funtts.__version__}")
        available_engines = funtts.get_available_engines()
        print(f"✅ 可用引擎: {available_engines}")
    except Exception as e:
        print(f"❌ 基础导入失败: {e}")
        return False

    # 测试Edge TTS（如果可用）
    if "edge" in available_engines:
        try:
            from funtts.tts.edge import EdgeTTS

            tts = EdgeTTS()
            voices = tts.list_voices(language="zh-CN")
            print(f"✅ Edge TTS: 找到{len(voices)}个中文语音")
        except Exception as e:
            print(f"⚠️  Edge TTS测试失败: {e}")

    # 测试eSpeak（如果可用）
    if "espeak" in available_engines:
        try:
            from funtts.tts.espeak import EspeakTTS

            tts = EspeakTTS()
            print("✅ eSpeak TTS: 安装正常")
        except Exception as e:
            print(f"⚠️  eSpeak TTS测试失败: {e}")

    print("🎉 安装测试完成！")
    return True


if __name__ == "__main__":
    test_installation()
```

### 语音生成测试

```python
#!/usr/bin/env python3
"""语音生成测试"""

import funtts
from funtts.models import TTSRequest


def test_speech_generation():
    """测试语音生成功能"""

    # 使用最可靠的引擎进行测试
    available_engines = funtts.get_available_engines()

    test_engines = []
    if "edge" in available_engines:
        test_engines.append("edge")
    if "espeak" in available_engines:
        test_engines.append("espeak")
    if "pyttsx3" in available_engines:
        test_engines.append("pyttsx3")

    if not test_engines:
        print("❌ 没有可用的TTS引擎")
        return False

    for engine_name in test_engines:
        try:
            print(f"🧪 测试{engine_name}引擎...")

            tts = funtts.create_tts(engine_name=engine_name)

            request = TTSRequest(
                text="这是FunTTS的安装测试。", output_dir="./test_output"
            )

            response = tts.synthesize(request)
            print(f"✅ {engine_name}: 生成成功 - {response.audio_file}")

        except Exception as e:
            print(f"❌ {engine_name}测试失败: {e}")

    print("🎉 语音生成测试完成！")


if __name__ == "__main__":
    test_speech_generation()
```

## 🚨 常见问题排除

### 1. 导入错误

**问题**: `ImportError: No module named 'funtts'`

**解决方案**:
```bash
# 确认安装
pip list | grep funtts

# 重新安装
pip uninstall funtts
pip install funtts-plus
```

### 2. Edge TTS网络问题

**问题**: `ConnectionError` 或超时错误

**解决方案**:
```python
# 设置代理（如需要）
import os

os.environ["HTTP_PROXY"] = "http://proxy:port"
os.environ["HTTPS_PROXY"] = "http://proxy:port"

# 增加超时时间
from funtts.tts.edge import EdgeTTS

tts = EdgeTTS(timeout=60)
```

### 3. Azure TTS认证失败

**问题**: `AuthenticationError`

**解决方案**:
```bash
# 检查环境变量
echo $AZURE_SPEECH_KEY
echo $AZURE_SPEECH_REGION

# 重新设置
export AZURE_SPEECH_KEY="your-correct-key"
export AZURE_SPEECH_REGION="your-correct-region"
```

### 4. GPU相关问题

**问题**: CUDA错误或GPU不可用

**解决方案**:
```bash
# 检查CUDA安装
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# 强制使用CPU
export CUDA_VISIBLE_DEVICES=""
```

### 5. 内存不足

**问题**: `OutOfMemoryError`

**解决方案**:
```python
# 使用轻量级引擎
from funtts.tts.espeak import EspeakTTS

tts = EspeakTTS()

# 或使用小模型
from funtts.tts.bark import BarkTTS

tts = BarkTTS(use_small_models=True)
```

## 🔄 升级指南

### 从旧版本升级

```bash
# 查看当前版本
pip show funtts

# 升级到最新版本
uv pip install --upgrade funtts

# 升级特定引擎
uv pip install --upgrade "funtts-plus[edge,azure]"
```

### 配置迁移

如果从旧版本升级，可能需要更新配置文件格式。请参考最新的配置示例。

## 📊 性能优化

### 1. 缓存配置

FunTTS 当前没有缓存目录环境变量；各引擎的模型缓存设置请参阅其各自的文档。

### 2. 并发处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor


async def batch_synthesis(texts, engine_name="edge"):
    """批量语音合成"""
    tts = funtts.create_tts(engine_name=engine_name)

    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = []
        for text in texts:
            request = TTSRequest(text=text)
            task = executor.submit(tts.synthesize, request)
            tasks.append(task)

        results = [task.result() for task in tasks]

    return results
```

### 3. 内存管理

```python
# 对于大批量处理，及时清理
import gc


def process_large_batch(texts):
    for i, text in enumerate(texts):
        # 处理文本
        result = process_text(text)

        # 每100个清理一次内存
        if i % 100 == 0:
            gc.collect()
```

## 🎯 生产环境部署

### 1. 系统服务

创建systemd服务文件 `/etc/systemd/system/funtts.service`:

```ini
[Unit]
Description=FunTTS Service
After=network.target

[Service]
Type=simple
User=funtts
WorkingDirectory=/opt/funtts
Environment=PATH=/opt/funtts/venv/bin
ExecStart=/opt/funtts/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. 负载均衡

使用Nginx进行负载均衡：

```nginx
upstream funtts_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://funtts_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 监控和日志

```python
# 配置日志
from farlog import configure, getLogger

configure("/var/log/funtts")
logger = getLogger("funtts")
```

## 📞 技术支持

如果遇到安装或部署问题，请：

1. 查看 [FAQ文档](FAQ.md)
2. 搜索 [GitHub Issues](https://github.com/farfarfun/funtts/issues)
3. 提交新的Issue，包含：
   - 系统信息 (`python --version`, `pip --version`)
   - 错误日志
   - 复现步骤

## 🎉 安装完成

恭喜！你已经成功安装了FunTTS。现在可以：

1. 查看 [快速开始指南](../README.md#快速开始)
2. 阅读 [TTS引擎选择指南](TTS_ENGINE_SELECTION_GUIDE.md)
3. 运行 [综合示例](../examples/comprehensive_example.py)
4. 探索各个引擎的详细文档

祝你使用愉快！🚀
