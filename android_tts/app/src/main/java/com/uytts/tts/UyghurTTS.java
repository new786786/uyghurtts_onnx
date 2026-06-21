package com.uytts.tts;

import android.content.Context;
import android.content.res.AssetManager;
import android.util.Log;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;

import java.io.*;
import java.nio.FloatBuffer;
import java.nio.LongBuffer;
import java.util.*;

/**
 * 维吾尔语 VITS TTS ONNX 推理引擎。
 * <p>
 * 模型输入:
 *   input         — int64 [1, seq_len]  文本 ID 序列(含 intersperse blank)
 *   input_lengths — int64 [1]           序列长度
 *   scales        — float32 [3]         [noise_scale, noise_scale_w, length_scale]
 * <p>
 * 模型输出:
 *   audio — float32 (最多 4D，squeeze 为 1D) — PCM 波形 [-1,1]
 */
public class UyghurTTS implements AutoCloseable {

    private static final String TAG = "UyghurTTS";
    public static final int SAMPLE_RATE = 22050;

    private final OrtEnvironment env;
    private OrtSession session;
    private final TextProcessor textProcessor;

    private float noiseScale = 0.337f;
    private float noiseScaleW = 0.9f;
    private float lengthScale = 1.0f;

    /**
     * @param context    Android Context
     * @param assetPath  ONNX 模型在 assets 中的路径，如 "tts/model.onnx"
     * @param numThreads 推理线程数
     */
    public UyghurTTS(Context context, String assetPath, int numThreads) throws Exception {
        env = OrtEnvironment.getEnvironment();
        textProcessor = new TextProcessor();

        OrtSession.SessionOptions opts = new OrtSession.SessionOptions();
        opts.setIntraOpNumThreads(numThreads);
        opts.setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT);

        File modelFile = copyAssetToCache(context, assetPath);
        session = env.createSession(modelFile.getAbsolutePath(), opts);
        Log.i(TAG, "ONNX model loaded: " + assetPath);
    }

    /**
     * 从文件系统路径加载模型（模型不在 assets 中时使用）。
     */
    public UyghurTTS(String modelPath, int numThreads) throws Exception {
        env = OrtEnvironment.getEnvironment();
        textProcessor = new TextProcessor();

        OrtSession.SessionOptions opts = new OrtSession.SessionOptions();
        opts.setIntraOpNumThreads(numThreads);
        opts.setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT);

        session = env.createSession(modelPath, opts);
        Log.i(TAG, "ONNX model loaded: " + modelPath);
    }

    /**
     * 设置合成参数。
     * @param noiseScale   噪声尺度 (默认 0.337)
     * @param noiseScaleW  噪声权重 (默认 0.9)
     * @param lengthScale  语速缩放 (默认 1.0，>1 慢，<1 快)
     */
    public void setScales(float noiseScale, float noiseScaleW, float lengthScale) {
        this.noiseScale = noiseScale;
        this.noiseScaleW = noiseScaleW;
        this.lengthScale = lengthScale;
    }

    /**
     * 合成语音（核心方法）。
     * @param text 维吾尔语文本
     * @return PCM 16-bit 音频数据 (22050Hz, mono)
     */
    public short[] synthesize(String text) throws OrtException {
        String processed = NumberConverter.convertNumbersInText(text);
        int[] textIds = textProcessor.textToSequence(processed);

        long[] idsFlat = new long[textIds.length];
        for (int i = 0; i < textIds.length; i++) idsFlat[i] = textIds[i];

        OnnxTensor inputTensor = OnnxTensor.createTensor(env,
                LongBuffer.wrap(idsFlat), new long[]{1, textIds.length});
        OnnxTensor lengthTensor = OnnxTensor.createTensor(env,
                LongBuffer.wrap(new long[]{textIds.length}), new long[]{1});
        OnnxTensor scalesTensor = OnnxTensor.createTensor(env,
                FloatBuffer.wrap(new float[]{noiseScale, lengthScale, noiseScaleW}),
                new long[]{3});

        Map<String, OnnxTensor> inputs = new HashMap<>();
        inputs.put("input", inputTensor);
        inputs.put("input_lengths", lengthTensor);
        inputs.put("scales", scalesTensor);

        OrtSession.Result result = session.run(inputs);

        float[] audio = extractAudio(result);

        short[] pcm16 = new short[audio.length];
        for (int i = 0; i < audio.length; i++) {
            pcm16[i] = (short) Math.max(-32768, Math.min(32767, audio[i] * 32767f));
        }

        inputTensor.close();
        lengthTensor.close();
        scalesTensor.close();
        result.close();

        return pcm16;
    }

    /**
     * 合成并返回 float32 PCM（如需进一步处理可使用此方法）。
     */
    public float[] synthesizeFloat(String text) throws OrtException {
        String processed = NumberConverter.convertNumbersInText(text);
        int[] textIds = textProcessor.textToSequence(processed);

        long[] idsFlat = new long[textIds.length];
        for (int i = 0; i < textIds.length; i++) idsFlat[i] = textIds[i];

        OnnxTensor inputTensor = OnnxTensor.createTensor(env,
                LongBuffer.wrap(idsFlat), new long[]{1, textIds.length});
        OnnxTensor lengthTensor = OnnxTensor.createTensor(env,
                LongBuffer.wrap(new long[]{textIds.length}), new long[]{1});
        OnnxTensor scalesTensor = OnnxTensor.createTensor(env,
                FloatBuffer.wrap(new float[]{noiseScale, lengthScale, noiseScaleW}),
                new long[]{3});

        Map<String, OnnxTensor> inputs = new HashMap<>();
        inputs.put("input", inputTensor);
        inputs.put("input_lengths", lengthTensor);
        inputs.put("scales", scalesTensor);

        OrtSession.Result result = session.run(inputs);
        float[] audio = extractAudio(result);

        inputTensor.close();
        lengthTensor.close();
        scalesTensor.close();
        result.close();

        return audio;
    }

    /**
     * 长文本分段合成（按标点分段 + 插入静音停顿）。
     */
    public short[] synthesizeLong(String text) throws OrtException {
        return synthesizeLong(text, getDefaultPauses());
    }

    public short[] synthesizeLong(String text, Map<String, Integer> pauseConfig) throws OrtException {
        String processed = NumberConverter.convertNumbersInText(text);
        List<String[]> segments = splitByPunctuation(processed, pauseConfig);

        List<short[]> allAudio = new ArrayList<>();
        for (String[] seg : segments) {
            String segText = seg[0];
            int pauseMs = Integer.parseInt(seg[1]);

            try {
                short[] audio = synthesize(segText);
                allAudio.add(audio);
                if (pauseMs > 0) {
                    allAudio.add(generateSilence(pauseMs));
                }
            } catch (Exception e) {
                Log.w(TAG, "Segment synthesis failed: " + segText, e);
            }
        }

        return concatenate(allAudio);
    }

    @Override
    public void close() {
        try {
            if (session != null) session.close();
        } catch (OrtException e) {
            Log.w(TAG, "Error closing session", e);
        }
    }

    // ==================== 内部方法 ====================

    private float[] extractAudio(OrtSession.Result result) throws OrtException {
        Object val = result.get(0).getValue();

        if (val instanceof float[][][][]) {
            return ((float[][][][]) val)[0][0][0];
        } else if (val instanceof float[][][]) {
            return ((float[][][]) val)[0][0];
        } else if (val instanceof float[][]) {
            return ((float[][]) val)[0];
        } else if (val instanceof float[]) {
            return (float[]) val;
        }
        throw new OrtException("Unexpected output shape");
    }

    private short[] generateSilence(int durationMs) {
        int numSamples = (int) (durationMs / 1000.0 * SAMPLE_RATE);
        return new short[numSamples];
    }

    private short[] concatenate(List<short[]> chunks) {
        int totalLen = 0;
        for (short[] c : chunks) totalLen += c.length;
        short[] result = new short[totalLen];
        int offset = 0;
        for (short[] c : chunks) {
            System.arraycopy(c, 0, result, offset, c.length);
            offset += c.length;
        }
        return result;
    }

    private List<String[]> splitByPunctuation(String text, Map<String, Integer> pauseConfig) {
        List<String[]> segments = new ArrayList<>();
        Set<String> puncts = new HashSet<>(pauseConfig.keySet());
        puncts.remove("\n");

        StringBuilder current = new StringBuilder();
        for (int i = 0; i < text.length(); i++) {
            String ch = String.valueOf(text.charAt(i));

            if (ch.equals("\n")) {
                String seg = current.toString().trim();
                if (!seg.isEmpty()) {
                    Integer pause = pauseConfig.getOrDefault("\n", 500);
                    segments.add(new String[]{seg, String.valueOf(pause)});
                }
                current.setLength(0);
            } else if (puncts.contains(ch)) {
                current.append(ch);
                String seg = current.toString().trim();
                if (!seg.isEmpty()) {
                    Integer pause = pauseConfig.getOrDefault(ch, 300);
                    segments.add(new String[]{seg, String.valueOf(pause)});
                }
                current.setLength(0);
            } else {
                current.append(ch);
            }
        }
        String remaining = current.toString().trim();
        if (!remaining.isEmpty()) {
            segments.add(new String[]{remaining, "0"});
        }
        return segments;
    }

    public static Map<String, Integer> getDefaultPauses() {
        Map<String, Integer> pauses = new HashMap<>();
        pauses.put("\u060C", 350); // ،
        pauses.put(",", 350);
        pauses.put("\u061B", 450); // ؛
        pauses.put(";", 450);
        pauses.put("\u061F", 550); // ؟
        pauses.put("?", 550);
        pauses.put("!", 550);
        pauses.put(".", 550);
        pauses.put(":", 300);
        pauses.put("\uFF1A", 300); // ：
        pauses.put("\u2026", 600); // …
        pauses.put("\n", 500);
        return pauses;
    }

    private File copyAssetToCache(Context context, String assetPath) throws IOException {
        File cacheFile = new File(context.getCacheDir(), assetPath.replace("/", "_"));
        if (cacheFile.exists() && cacheFile.length() > 0) {
            return cacheFile;
        }
        try (InputStream is = context.getAssets().open(assetPath);
             OutputStream os = new FileOutputStream(cacheFile)) {
            byte[] buf = new byte[8192];
            int len;
            while ((len = is.read(buf)) != -1) {
                os.write(buf, 0, len);
            }
        }
        return cacheFile;
    }
}
