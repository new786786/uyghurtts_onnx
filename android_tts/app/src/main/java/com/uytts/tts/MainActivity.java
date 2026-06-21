package com.uytts.tts;

import android.os.Bundle;
import android.os.Environment;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.File;

public class MainActivity extends AppCompatActivity {

    private UyghurTTS tts;
    private AudioPlayer player;

    private EditText editText;
    private Button btnSynthesize;
    private Button btnStop;
    private Button btnSave;
    private ProgressBar progressBar;
    private TextView statusText;
    private SeekBar speedSeekBar;
    private TextView speedLabel;

    private short[] lastAudio;
    private float currentSpeed = 1.0f;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        editText = findViewById(R.id.editText);
        btnSynthesize = findViewById(R.id.btnSynthesize);
        btnStop = findViewById(R.id.btnStop);
        btnSave = findViewById(R.id.btnSave);
        progressBar = findViewById(R.id.progressBar);
        statusText = findViewById(R.id.statusText);
        speedSeekBar = findViewById(R.id.speedSeekBar);
        speedLabel = findViewById(R.id.speedLabel);

        player = new AudioPlayer();
        btnSynthesize.setEnabled(false);
        btnSave.setEnabled(false);

        // 默认维吾尔语示例文本
         editText.setText("ئاۋاز بىرىكتۇرۇش سېستىمسى");

        speedSeekBar.setMax(100);
        speedSeekBar.setProgress(50);
        speedSeekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar sb, int progress, boolean fromUser) {
                currentSpeed = 0.5f + progress / 100f;
                speedLabel.setText(String.format("%.2f", currentSpeed));
            }
            @Override public void onStartTrackingTouch(SeekBar sb) {}
            @Override public void onStopTrackingTouch(SeekBar sb) {}
        });

        statusText.setText("\u6A21\u578B\u52A0\u8F7D\u4E2D...");
        progressBar.setVisibility(View.VISIBLE);

        new Thread(() -> {
            try {
                tts = new UyghurTTS(MainActivity.this, "tts/model.onnx", 4);
                runOnUiThread(() -> {
                    statusText.setText("\u5F15\u64CE\u5C31\u7EEA\uFF0C\u8BF7\u8F93\u5165\u7EF4\u543E\u5C14\u8BED\u6587\u672C");
                    btnSynthesize.setEnabled(true);
                    progressBar.setVisibility(View.GONE);
                });
            } catch (Exception e) {
                e.printStackTrace();
                runOnUiThread(() -> {
                    statusText.setText("\u6A21\u578B\u52A0\u8F7D\u5931\u8D25: " + e.getMessage());
                    progressBar.setVisibility(View.GONE);
                });
            }
        }).start();

        btnSynthesize.setOnClickListener(v -> doSynthesize());
        btnStop.setOnClickListener(v -> player.stop());
        btnSave.setOnClickListener(v -> doSave());
    }

    private void doSynthesize() {
        String text = editText.getText().toString().trim();
        if (text.isEmpty()) {
            Toast.makeText(this, "\u8BF7\u8F93\u5165\u6587\u672C", Toast.LENGTH_SHORT).show();
            return;
        }
        if (tts == null) return;

        btnSynthesize.setEnabled(false);
        statusText.setText("\u6B63\u5728\u5408\u6210...");
        progressBar.setVisibility(View.VISIBLE);

        new Thread(() -> {
            long start = System.currentTimeMillis();
            try {
                tts.setScales(0.337f, 0.9f, currentSpeed);

                short[] audio;
                if (text.length() > 100) {
                    audio = tts.synthesizeLong(text);
                } else {
                    audio = tts.synthesize(text);
                }
                lastAudio = audio;
                long elapsed = System.currentTimeMillis() - start;
                float duration = audio.length / (float) UyghurTTS.SAMPLE_RATE;

                runOnUiThread(() -> {
                    statusText.setText(String.format(
                            "\u5408\u6210\u5B8C\u6210 | \u8017\u65F6 %.1f\u79D2 | \u97F3\u9891 %.1f\u79D2",
                            elapsed / 1000f, duration));
                    progressBar.setVisibility(View.GONE);
                    btnSynthesize.setEnabled(true);
                    btnSave.setEnabled(true);
                    player.play(audio, UyghurTTS.SAMPLE_RATE);
                });
            } catch (Exception e) {
                e.printStackTrace();
                runOnUiThread(() -> {
                    statusText.setText("\u5408\u6210\u5931\u8D25: " + e.getMessage());
                    progressBar.setVisibility(View.GONE);
                    btnSynthesize.setEnabled(true);
                });
            }
        }).start();
    }

    private void doSave() {
        if (lastAudio == null) return;
        try {
            File dir = getExternalFilesDir(Environment.DIRECTORY_MUSIC);
            if (dir == null) dir = getCacheDir();
            String path = new File(dir, "tts_output_" + System.currentTimeMillis() + ".wav")
                    .getAbsolutePath();
            AudioPlayer.saveWav(lastAudio, UyghurTTS.SAMPLE_RATE, path);
            Toast.makeText(this, "\u5DF2\u4FDD\u5B58: " + path, Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "\u4FDD\u5B58\u5931\u8D25: " + e.getMessage(),
                    Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        player.stop();
        if (tts != null) tts.close();
    }
}
