# TTS引擎开发规范

本文档定义了FunTTS项目中TTS引擎的开发规范和标准化结构。

## 📋 目录结构规范

每个TTS引擎必须遵循以下目录结构：

```
src/funtts/tts/{engine_name}/
├── __init__.py          # 模块初始化，导出主要类
├── tts.py              # TTS引擎实现（必需）
├── README.md           # 引擎说明文档（必需）
└── {optional_files}    # 其他可选文件
```

### 文件说明

- **`__init__.py`**: 模块入口，导出TTS类
- **`tts.py`**: TTS引擎的核心实现，继承BaseTTS
- **`README.md`**: 引擎的详细说明文档
- **可选文件**: 根据引擎需要添加的辅助文件

## 🏗️ 代码实现规范

### 1. TTS类命名规范

```python
# 类名格式: {EngineName}TTS
class EdgeTTS(BaseTTS):      # ✅ 正确
class AzureTTS(BaseTTS):     # ✅ 正确
class EspeakTTS(BaseTTS):    # ✅ 正确
class Pyttsx3TTS(BaseTTS):   # ✅ 正确

class EdgeTts(BaseTTS):      # ❌ 错误
class edge_tts(BaseTTS):     # ❌ 错误
```

### 2. 文件头部规范

每个`tts.py`文件必须包含以下头部：

```python
"""
{引擎名称} TTS引擎实现
支持{主要功能描述}
"""

from typing import List, Optional
from farlog import getLogger

from ...base import BaseTTS
from ...models import TTSRequest, TTSResponse, VoiceInfo

logger = getLogger("funtts.tts.{engine_name}")
```

### 3. 类实现规范

```python
class {EngineName}TTS(BaseTTS):
    """
    {引擎名称} TTS引擎
    
    特性:
    - 功能1描述
    - 功能2描述
    - 功能3描述
    
    依赖:
    - 依赖包1: 版本要求
    - 依赖包2: 版本要求
    """
    
    def __init__(self, voice_name: str = "default", **kwargs):
        """
        初始化{引擎名称}TTS引擎
        
        Args:
            voice_name: 默认语音名称
            **kwargs: 其他配置参数
        """
        super().__init__(voice_name, **kwargs)
        # 引擎特定的初始化逻辑
        
    def synthesize(self, request: TTSRequest) -> TTSResponse:
        """
        语音合成实现
        
        Args:
            request: TTS请求对象
            
        Returns:
            TTSResponse: TTS响应对象
        """
        # 必须实现的核心方法
        pass
        
    def list_voices(self, language: str = None) -> List[VoiceInfo]:
        """
        获取可用语音列表
        
        Args:
            language: 语言过滤条件
            
        Returns:
            List[VoiceInfo]: 语音信息列表
        """
        # 必须实现的方法
        pass
        
    def is_voice_available(self, voice_name: str) -> bool:
        """
        检查语音是否可用
        
        Args:
            voice_name: 语音名称
            
        Returns:
            bool: 是否可用
        """
        # 必须实现的方法
        pass
        
    def _validate_request(self, request: TTSRequest) -> bool:
        """
        验证请求参数（可选实现）
        
        Args:
            request: TTS请求对象
            
        Returns:
            bool: 验证结果
        """
        # 可选实现的辅助方法
        return True
        
    def _create_voice_info(self, voice_data: dict) -> VoiceInfo:
        """
        创建VoiceInfo对象（辅助方法）
        
        Args:
            voice_data: 原始语音数据
            
        Returns:
            VoiceInfo: 语音信息对象
        """
        # 辅助方法示例
        return VoiceInfo(
            name=voice_data.get("name", ""),
            display_name=voice_data.get("display_name", ""),
            language=voice_data.get("language", ""),
            gender=voice_data.get("gender", "unknown"),
            engine=self.__class__.__name__.lower().replace("tts", "")
        )
```

### 4. 错误处理规范

```python
def synthesize(self, request: TTSRequest) -> TTSResponse:
    """语音合成实现"""
    try:
        # 参数验证
        if not self._validate_request(request):
            return TTSResponse(
                success=False,
                request=request,
                error_message="请求参数验证失败",
                error_code="INVALID_REQUEST",
            )

        # 语音检查
        if not self.is_voice_available(request.voice_name):
            return TTSResponse(
                success=False,
                request=request,
                error_message=f"语音不可用: {request.voice_name}",
                error_code="VOICE_NOT_AVAILABLE",
            )

        # 核心合成逻辑
        start_time = time.time()

        # ... 实现合成逻辑 ...

        processing_time = time.time() - start_time

        # 成功响应
        return TTSResponse(
            success=True,
            request=request,
            audio_file=request.output_file,
            duration=audio_duration,
            voice_used=actual_voice_used,
            processing_time=processing_time,
            engine_info={
                "engine": self.__class__.__name__.lower().replace("tts", ""),
                "version": "1.0.0",
            },
        )

    except ImportError as e:
        logger.error(f"依赖包未安装: {e}")
        return TTSResponse(
            success=False,
            request=request,
            error_message=f"缺少依赖包: {str(e)}",
            error_code="MISSING_DEPENDENCY",
        )

    except Exception as e:
        logger.error(f"语音合成失败: {e}")
        return TTSResponse(
            success=False,
            request=request,
            error_message=str(e),
            error_code="SYNTHESIS_ERROR",
        )
```

### 5. 日志记录规范

```python
# 使用统一的日志记录器
logger = getLogger("funtts.tts.{engine_name}")

# 日志级别使用规范
logger.debug("调试信息：详细的执行过程")
logger.info("一般信息：重要的状态变化")
logger.success("成功信息：操作成功完成")  # 使用funutil的success级别
logger.warning("警告信息：潜在问题")
logger.error("错误信息：操作失败")

# 示例
logger.info(f"开始合成语音，文本长度: {len(request.text)}")
logger.success(f"语音合成完成: {response.audio_file}")
logger.error(f"合成失败: {error_message}")
```

## 📝 README文档规范

每个引擎的`README.md`必须包含以下章节：

```markdown
# {引擎名称} TTS引擎

## 概述

简要描述引擎的特点和用途。

## 特性

- ✅ 特性1
- ✅ 特性2  
- ❌ 不支持的特性

## 依赖要求

### Python包依赖

```bash
pip install package1>=version1
pip install package2>=version2
```

### 系统依赖

描述需要的系统级依赖。

## 配置说明

### 基本配置

```python
config = {"param1": "value1", "param2": "value2"}
```

### 高级配置

详细的配置选项说明。

## 使用示例

### 基本使用

```python
from funtts import TTSFactory, TTSRequest

# 创建引擎实例
tts = TTSFactory.create_tts("{engine_name}", "voice_name")

# 合成语音
request = TTSRequest(text="测试文本", voice_name="voice_name", output_file="output.wav")
response = tts.synthesize(request)
```

### 高级使用

更复杂的使用场景示例。

## 可用语音

| 语音名称 | 显示名称 | 语言 | 性别 | 说明 |
|---------|---------|------|------|------|
| voice1  | 语音1   | zh-CN | female | 描述 |
| voice2  | 语音2   | en-US | male   | 描述 |

## 限制说明

- 限制1
- 限制2

## 故障排除

### 常见问题

**Q: 问题描述**
A: 解决方案

## 更新日志

### v1.0.0
- 初始版本
```

## 🔧 __init__.py规范

```python
"""
{引擎名称} TTS引擎模块
"""

from .tts import {EngineName}TTS

__all__ = ["{EngineName}TTS"]
```

## ✅ 质量检查清单

在提交引擎实现前，请确保：

### 代码质量
- [ ] 继承自BaseTTS基类
- [ ] 实现所有必需的抽象方法
- [ ] 遵循命名规范
- [ ] 包含完整的类型注解
- [ ] 添加详细的文档字符串
- [ ] 实现适当的错误处理
- [ ] 使用统一的日志记录

### 文件结构
- [ ] 包含tts.py实现文件
- [ ] 包含README.md文档
- [ ] 包含__init__.py导出文件
- [ ] 文件结构符合规范

### 功能测试
- [ ] 基本语音合成功能正常
- [ ] 语音列表获取正常
- [ ] 语音可用性检查正常
- [ ] 错误处理机制有效
- [ ] 日志记录完整

### 文档完整性
- [ ] README包含所有必需章节
- [ ] 代码注释清晰完整
- [ ] 使用示例可运行
- [ ] 依赖说明准确

## 🚀 集成步骤

1. **创建引擎目录**
   ```bash
   mkdir -p src/funtts/tts/{engine_name}
   ```

2. **实现核心文件**
   - 创建`tts.py`实现文件
   - 创建`README.md`文档
   - 创建`__init__.py`导出文件

3. **注册引擎**
   在`src/funtts/factory.py`中注册新引擎：
   ```python
   from .tts.{engine_name} import {EngineName}TTS
   
   # 在_default_engines中添加
   "{engine_name}": {EngineName}TTS,
   ```

4. **更新依赖**
   在`pyproject.toml`中添加可选依赖：
   ```toml
   {engine_name} = [
       "dependency1>=version1",
       "dependency2>=version2",
   ]
   ```

5. **添加测试**
   创建对应的测试文件验证功能。

## 📚 参考示例

参考现有的引擎实现：
- `src/funtts/tts/edge/` - Edge TTS实现
- `src/funtts/tts/azure/` - Azure TTS实现
- `src/funtts/tts/espeak/` - eSpeak实现
- `src/funtts/tts/pyttsx3/` - pyttsx3实现

遵循这些规范可以确保所有TTS引擎具有一致的接口和良好的可维护性。
