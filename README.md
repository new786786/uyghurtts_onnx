# UighurTTS ONNX — 维吾尔语神经网络语音合成

ئۇيغۇرچە نېرۋا تور ئاۋاز بىرىكتۈرۈش سىستېمىسى

基于 ONNX 推理的维吾尔语 TTS 系统，支持 Python 服务端、Web API 和 Android 客户端。

## 功能特点

- **ONNX 推理**：支持多个 TTS 模型（hawagul、hawahan、xjsdn 等）
- **声音克隆**：`clone_onnx` 模块提供语音克隆能力
- **Web API**：Flask 服务端，提供 REST 接口
- **Android 客户端**：原生 Android TTS 应用
- **多模型切换**：支持多个预训练模型

## 项目结构

```
├── uytts.py              # TTS 核心引擎
├── tts.py / utts.py       # TTS 变体实现
├── app.py                 # Flask Web API
├── main.py                # 主程序入口
├── new.py                 # 新版实现
├── text/                  # 文本处理模块
│   ├── __init__.py
│   ├── symbols.py
│   └── uyclean.py
├── model_parts/           # 根目录模型分片
├── tts_onnx/              # TTS 模型
│   └── model_parts/       # TTS 模型分片
├── clone_onnx/            # 克隆模型
│   └── model_parts/       # 克隆模型分片
├── android_tts/           # Android 客户端
├── templates/             # Web 模板
├── static/                # 静态资源
└── requirements.txt       # Python 依赖
```

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/new786786/uyghurtts_onnx.git
cd uyghurtts_onnx
```

### 2. 合并模型文件

模型文件因 GitHub 限制拆分为分片，需先合并：

```bash
python merge_models.py
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行

```bash
# Web API
python app.py

# 直接合成
python main.py
```

## 模型说明

| 模型 | 位置 | 说明 |
|------|------|------|
| vec-768-layer-12.onnx | 根目录 | 语音特征提取模型 |
| 22k_hawagul.onnx | 根目录 | 22kHz hawagul 语音模型 |
| model.onnx / hawahan.onnx / xjsdn.onnx | tts_onnx/ | TTS 合成模型 |
| 1.onnx / 2.onnx | clone_onnx/ | 声音克隆模型 |
