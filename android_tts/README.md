# 维吾尔语 TTS Android 应用

基于 ONNX Runtime 的维吾尔语语音合成 Android 应用，支持系统级 TTS 引擎注册。

---

## 项目结构

```
android_tts/
├── app/src/main/
│   ├── java/com/uytts/tts/
│   │   ├── UyghurTTS.java          ← 核心 ONNX 推理引擎
│   │   ├── UyghurTTSService.java   ← 系统级 TTS 引擎服务
│   │   ├── TextProcessor.java      ← 维吾尔语文本→ID序列 (symbols.py 移植)
│   │   ├── NumberConverter.java    ← 数字→维吾尔语文字 (uyclean.py 移植)
│   │   ├── AudioPlayer.java       ← PCM 播放 + WAV 保存
│   │   └── MainActivity.java      ← 演示界面
│   ├── res/
│   │   ├── layout/activity_main.xml  ← 界面布局
│   │   ├── xml/tts_engine.xml        ← TTS 引擎元数据
│   │   └── values/strings.xml
│   ├── assets/tts/
│   │   └── model.onnx               ← 需要手动放入
│   └── AndroidManifest.xml
├── app/build.gradle
├── build.gradle
├── settings.gradle
├── gradle.properties
└── README.md
```

---

## 模型信息

| 项目 | 值 |
|------|-----|
| 模型文件 | `F:\uytts\tts_onnx\model.onnx` |
| 模型架构 | VITS (端到端 TTS) |
| 模型大小 | ~122 MB |
| 采样率 | 22050 Hz |
| 声道 | 单声道 (Mono) |
| 输出格式 | PCM 16-bit |
| 支持语言 | 维吾尔语 |
| 最低 Android 版本 | API 26 (Android 8.0) |

### 模型输入输出

| 输入名 | 类型 | 形状 | 说明 |
|--------|------|------|------|
| `input` | int64 | [1, seq_len] | 文本 ID 序列（含 blank 间隔符） |
| `input_lengths` | int64 | [1] | 序列长度 |
| `scales` | float32 | [3] | [noise_scale, noise_scale_w, length_scale] |

| 输出名 | 类型 | 形状 | 说明 |
|--------|------|------|------|
| audio | float32 | [1,1,1,N] | PCM 波形 [-1, 1]，squeeze 后为 1D |

---

## 快速开始

### 第一步：放置模型文件

将 ONNX 模型复制到 assets 目录：

```
复制 F:\uytts\tts_onnx\model.onnx
到   android_tts\app\src\main\assets\tts\model.onnx
```

也可以使用 `hawahan.onnx`，只需相应修改加载路径。

### 第二步：用 Android Studio 打开项目

1. 打开 Android Studio → **Open** → 选择 `android_tts` 文件夹
2. 等待 Gradle 同步完成
3. 连接 Android 设备或启动模拟器
4. 点击 **Run**

### 第三步：在系统中启用 TTS 引擎

安装 APK 后：

1. 打开系统设置 → **语言和输入** → **文字转语音**
2. 在 TTS 引擎列表中选择 **"ئۇيغۇر تىلى TTS"**
3. 所有使用 Android TTS 的应用即可调用

---

## 功能清单

| 功能 | 支持 | 说明 |
|------|------|------|
| 系统级 TTS 引擎 | ✅ | 注册为系统 TTS，其他 App 可调用 |
| 独立 App 使用 | ✅ | 直接集成到任何 Android 项目 |
| 语速调节 | ✅ | 响应系统语速设置 / 手动调节 |
| 长文本分段合成 | ✅ | 自动按标点分句 + 插入停顿 |
| 数字转文字 | ✅ | 自动转换（整数、小数、年份、序数词） |
| WAV 文件保存 | ✅ | 导出 22050Hz 16-bit WAV |
| WAV 字节流输出 | ✅ | 适用于网络传输 |
| 外部模型加载 | ✅ | 支持从 SD 卡等路径加载 |

---

## 文件说明

### UyghurTTS.java — 核心推理引擎

主要方法：

| 方法 | 说明 |
|------|------|
| `UyghurTTS(context, assetPath, threads)` | 从 assets 加载模型初始化 |
| `UyghurTTS(modelPath, threads)` | 从文件路径加载模型 |
| `synthesize(text)` | 合成短文本，返回 `short[]` PCM |
| `synthesizeFloat(text)` | 合成短文本，返回 `float[]` PCM |
| `synthesizeLong(text)` | 长文本分段合成 |
| `setScales(noise, noiseW, speed)` | 设置噪声和语速参数 |
| `close()` | 释放模型资源 |

### UyghurTTSService.java — 系统 TTS 服务

继承 `android.speech.tts.TextToSpeechService`，自动注册为系统 TTS 引擎。

特性：
- 后台自动加载 ONNX 模型
- 响应系统语速设置
- 长文本自动分段
- 语言标识：`ug` (维吾尔语)

### TextProcessor.java — 文本预处理

完整移植 Python 端 `text/symbols.py` 和 `text/__init__.py`：
- 符号表：PAD + 标点(`;:,.!?¡¿—…"«»"" `) + 字母(拉丁+维吾尔) + IPA音标
- 清理：小写转换 + 空白合并
- intersperse：在每个 token 之间插入 blank (ID=0)

### NumberConverter.java — 数字转换

完整移植 Python 端 `text/uyclean.py`：

| 输入格式 | 输出示例 |
|---------|---------|
| `123` → | بىر يۈز يىگىرمە ئۈچ |
| `0.68` → | نۆل پۈتۈن نۇقتا ئالتە سەككىز |
| `2026-يىللىق` → | ئىككى مىڭ يىگىرمە ئالتە ىنچى يىللىق |
| `16-ماي` → | ئون ئالتە-ماي |

### AudioPlayer.java — 音频播放

| 方法 | 说明 |
|------|------|
| `play(pcmData, sampleRate)` | 播放 PCM 16-bit 音频 |
| `stop()` | 停止播放 |
| `saveWav(pcm, rate, path)` | 保存为 WAV 文件 |
| `toWavBytes(pcm, rate)` | 转换为 WAV 字节数组 |

---

## API 使用示例

### 方式一：直接在 App 中使用

```java
// 1. 初始化（在后台线程，约 3-8 秒）
UyghurTTS tts = new UyghurTTS(context, "tts/model.onnx", 4);

// 2. 合成语音
short[] audio = tts.synthesize("ياخشىمۇسىز دۇنيا!");

// 3. 播放
AudioPlayer player = new AudioPlayer();
player.play(audio, UyghurTTS.SAMPLE_RATE);  // 22050Hz

// 4. 保存为 WAV
AudioPlayer.saveWav(audio, UyghurTTS.SAMPLE_RATE, "/sdcard/output.wav");

// 5. 长文本分段合成
short[] longAudio = tts.synthesizeLong("长段维吾尔语文本...");

// 6. 调节语速（>1 慢，<1 快）
tts.setScales(0.337f, 0.9f, 0.8f);  // 加速 20%

// 7. 释放资源
tts.close();
```

### 方式二：作为系统 TTS 被其他 App 调用

```java
// 在其他 App 中指定使用你的 TTS 引擎
TextToSpeech tts = new TextToSpeech(context, status -> {
    if (status == TextToSpeech.SUCCESS) {
        tts.setLanguage(new Locale("ug", "CN"));
        tts.speak("ياخشىمۇسىز", TextToSpeech.QUEUE_FLUSH, null, null);
    }
}, "com.uytts.tts");  // 指定引擎包名
```

### 方式三：从外部路径加载模型

```java
// 适用于模型不打包在 APK 中的场景（按需下载）
UyghurTTS tts = new UyghurTTS("/sdcard/Download/model.onnx", 4);
```

---

## 依赖配置

### build.gradle (app)

```gradle
dependencies {
    implementation 'com.microsoft.onnxruntime:onnxruntime-android:1.19.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
}

android {
    aaptOptions {
        noCompress "onnx"
    }
}
```

---

## 性能参考

| 设备 | 初始化时间 | 短句合成 (~20字) | 长段合成 (~200字) |
|------|-----------|-----------------|------------------|
| 中端手机 (骁龙 778G) | ~5s | ~1-2s | ~5-15s |
| 高端手机 (骁龙 8 Gen2) | ~3s | <1s | ~3-8s |
| 低端手机 | ~8-12s | ~3-5s | ~15-30s |

---

## 注意事项

1. **内存**：模型加载约占 300-500MB 内存，已在 AndroidManifest 中设置 `android:largeHeap="true"`
2. **线程**：合成必须在后台线程执行，不要在主线程调用 `synthesize()`
3. **模型体积**：122MB 模型会增大 APK 体积，建议：
   - 使用 Android App Bundle (AAB) 分发
   - 或首次使用时从服务器下载模型到本地
4. **两个模型**：`model.onnx` 和 `hawahan.onnx` 都可用，只需改加载路径
5. **系统 TTS**：安装后需要在系统设置中手动选择引擎才生效

---

## 合成流程

```
1. 输入维吾尔语文本
2. NumberConverter: 数字→维吾尔语文字（2026→ئىككى مىڭ يىگىرمە ئالتە）
3. TextProcessor:
   a. basic_cleaners: 小写 + 空白合并
   b. 字符→符号ID映射
   c. intersperse: 插入 blank 间隔符
4. UyghurTTS (ONNX Runtime):
   输入: text_ids[1,N], lengths[1], scales[3]
   输出: float32 音频波形
5. 后处理: float32 → int16 PCM
6. AudioPlayer: 播放 或 保存 WAV
```
