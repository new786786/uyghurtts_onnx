package com.uytts.tts;

import android.speech.tts.SynthesisCallback;
import android.speech.tts.SynthesisRequest;
import android.speech.tts.TextToSpeech;
import android.speech.tts.TextToSpeechService;
import android.speech.tts.Voice;
import android.util.Log;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Android 系统级 TTS 引擎服务。
 * 安装后可在系统设置 → 语言和输入 → 文字转语音 中选择本引擎，
 * 所有使用 Android TextToSpeech API 的应用均可调用。
 */
public class UyghurTTSService extends TextToSpeechService {

    private static final String TAG = "UyghurTTSService";

    private static final Locale UYGHUR_LOCALE = new Locale("ug");
    private static final String VOICE_NAME = "ug-CN-vits";

    private UyghurTTS ttsEngine;
    private volatile boolean engineReady = false;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.i(TAG, "Service created, loading ONNX model...");
        new Thread(() -> {
            try {
                ttsEngine = new UyghurTTS(UyghurTTSService.this, "tts/model.onnx", 4);
                engineReady = true;
                Log.i(TAG, "ONNX model loaded successfully");
            } catch (Exception e) {
                Log.e(TAG, "Failed to load ONNX model", e);
            }
        }).start();
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (ttsEngine != null) {
            ttsEngine.close();
            ttsEngine = null;
        }
        engineReady = false;
    }

    @Override
    protected int onIsLanguageAvailable(String lang, String country, String variant) {
        if ("ug".equals(lang)) {
            return TextToSpeech.LANG_AVAILABLE;
        }
        return TextToSpeech.LANG_NOT_SUPPORTED;
    }

    @Override
    protected String[] onGetLanguage() {
        return new String[]{"ug", "", ""};
    }

    @Override
    protected int onLoadLanguage(String lang, String country, String variant) {
        return onIsLanguageAvailable(lang, country, variant);
    }

    @Override
    public List<Voice> onGetVoices() {
        List<Voice> voices = new ArrayList<>();
        Set<String> features = new HashSet<>();
        voices.add(new Voice(VOICE_NAME, UYGHUR_LOCALE,
                Voice.QUALITY_VERY_HIGH, Voice.LATENCY_NORMAL,
                false, features));
        return voices;
    }

    @Override
    public int onLoadVoice(String voiceName) {
        if (VOICE_NAME.equals(voiceName)) {
            return TextToSpeech.SUCCESS;
        }
        return TextToSpeech.ERROR;
    }

    @Override
    protected void onStop() {
    }

    @Override
    protected synchronized void onSynthesizeText(SynthesisRequest request,
                                                  SynthesisCallback callback) {
        if (!engineReady || ttsEngine == null) {
            Log.w(TAG, "Engine not ready");
            callback.error();
            return;
        }

        CharSequence textCs = request.getCharSequenceText();
        if (textCs == null) textCs = request.getText();
        if (textCs == null || textCs.length() == 0) {
            callback.done();
            return;
        }
        String text = textCs.toString();

        float lengthScale = 1.0f;
        int requestRate = request.getSpeechRate();
        if (requestRate > 0) {
            lengthScale = 100f / requestRate;
            lengthScale = Math.max(0.5f, Math.min(lengthScale, 2.0f));
        }
        ttsEngine.setScales(0.337f, 0.9f, lengthScale);

        callback.start(UyghurTTS.SAMPLE_RATE,
                android.media.AudioFormat.ENCODING_PCM_16BIT,
                1 /* mono */);

        try {
            short[] audio;
            if (text.length() > 100) {
                audio = ttsEngine.synthesizeLong(text);
            } else {
                audio = ttsEngine.synthesize(text);
            }

            byte[] pcmBytes = shortArrayToBytes(audio);

            final int CHUNK_SIZE = 8192;
            int offset = 0;
            while (offset < pcmBytes.length) {
                int len = Math.min(CHUNK_SIZE, pcmBytes.length - offset);
                int written = callback.audioAvailable(pcmBytes, offset, len);
                if (written != TextToSpeech.SUCCESS) {
                    Log.w(TAG, "audioAvailable returned error");
                    break;
                }
                offset += len;
            }
            callback.done();

        } catch (Exception e) {
            Log.e(TAG, "Synthesis error", e);
            callback.error();
        }
    }

    private static byte[] shortArrayToBytes(short[] shorts) {
        byte[] bytes = new byte[shorts.length * 2];
        for (int i = 0; i < shorts.length; i++) {
            bytes[i * 2] = (byte) (shorts[i] & 0xFF);
            bytes[i * 2 + 1] = (byte) ((shorts[i] >> 8) & 0xFF);
        }
        return bytes;
    }
}
