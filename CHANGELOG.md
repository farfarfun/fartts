# Changelog

## 0.1.21

### 新增

- 增加 `uv.lock`，并使用 Ruff 统一代码检查与格式化。

### 修复

- 修复 Bark、Coqui、IndexTTS2、Kitten、Pyttsx3 和 Tortoise 引擎因未实现 `_synthesize` 而无法实例化的问题。
- 修复 Tortoise 与 Coqui 的字幕模块导入，并为字幕保存失败补充上下文日志。

### 变更

- 项目整体由 `funtts` / `funtts-plus` 更名为 `fartts`，构建后端迁移至 Hatchling，日志统一改用 `farlog`。
- 迁移方法：安装 `fartts`，并将代码中的 `import funtts` / `from funtts ...` 改为 `import fartts` / `from fartts ...`。

### 废弃

- `funtts-plus` 发布名和 `funtts` 导入名停止使用，不提供兼容别名。

## 0.1.20 及更早版本

早期版本未维护 CHANGELOG，具体变更参见 git 提交历史。
