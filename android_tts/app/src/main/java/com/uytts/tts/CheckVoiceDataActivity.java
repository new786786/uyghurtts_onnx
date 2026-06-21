package com.uytts.tts;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;

import java.util.ArrayList;

/**
 * 系统通过此 Activity 检测引擎支持哪些语言。
 * 响应 android.speech.tts.engine.CHECK_TTS_DATA，
 * 返回已安装的语言列表，使系统 TTS 设置中出现语言选项。
 */
public class CheckVoiceDataActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ArrayList<String> available = new ArrayList<>();
        available.add("ug");

        ArrayList<String> unavailable = new ArrayList<>();

        Intent result = new Intent();
        result.putStringArrayListExtra(TextToSpeech.Engine.EXTRA_AVAILABLE_VOICES, available);
        result.putStringArrayListExtra(TextToSpeech.Engine.EXTRA_UNAVAILABLE_VOICES, unavailable);

        setResult(TextToSpeech.Engine.CHECK_VOICE_DATA_PASS, result);
        finish();
    }
}
