package com.uytts.tts;

import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioTrack;
import android.util.Log;

import java.io.*;

/**
 * PCM 音频播放与 WAV 文件保存工具。
 */
public class AudioPlayer {

    private static final String TAG = "AudioPlayer";
    private AudioTrack audioTrack;

    /**
     * 播放 PCM 16-bit 音频。
     */
    public void play(short[] pcmData, int sampleRate) {
        stop();

        int bufSize = AudioTrack.getMinBufferSize(
                sampleRate,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT);

        audioTrack = new AudioTrack.Builder()
                .setAudioAttributes(new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build())
                .setAudioFormat(new AudioFormat.Builder()
                        .setSampleRate(sampleRate)
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                        .build())
                .setBufferSizeInBytes(Math.max(bufSize, pcmData.length * 2))
                .setTransferMode(AudioTrack.MODE_STATIC)
                .build();

        audioTrack.write(pcmData, 0, pcmData.length);
        audioTrack.play();
    }

    /**
     * 停止播放并释放资源。
     */
    public void stop() {
        if (audioTrack != null) {
            try {
                if (audioTrack.getPlayState() == AudioTrack.PLAYSTATE_PLAYING) {
                    audioTrack.stop();
                }
                audioTrack.release();
            } catch (Exception e) {
                Log.w(TAG, "Error stopping AudioTrack", e);
            }
            audioTrack = null;
        }
    }

    /**
     * 将 PCM 16-bit 音频保存为 WAV 文件。
     */
    public static void saveWav(short[] pcmData, int sampleRate, String filePath)
            throws IOException {
        int dataSize = pcmData.length * 2;
        int byteRate = sampleRate * 2; // 16bit mono = 2 bytes/sample

        try (DataOutputStream dos = new DataOutputStream(
                new BufferedOutputStream(new FileOutputStream(filePath)))) {

            // RIFF header
            dos.writeBytes("RIFF");
            dos.writeInt(Integer.reverseBytes(36 + dataSize));
            dos.writeBytes("WAVE");

            // fmt chunk
            dos.writeBytes("fmt ");
            dos.writeInt(Integer.reverseBytes(16));        // chunk size
            dos.writeShort(Short.reverseBytes((short) 1)); // PCM
            dos.writeShort(Short.reverseBytes((short) 1)); // mono
            dos.writeInt(Integer.reverseBytes(sampleRate));
            dos.writeInt(Integer.reverseBytes(byteRate));
            dos.writeShort(Short.reverseBytes((short) 2)); // block align
            dos.writeShort(Short.reverseBytes((short) 16)); // bits per sample

            // data chunk
            dos.writeBytes("data");
            dos.writeInt(Integer.reverseBytes(dataSize));
            for (short sample : pcmData) {
                dos.writeShort(Short.reverseBytes(sample));
            }
        }
    }

    /**
     * 将 PCM 16-bit 音频保存为 WAV 字节数组（用于网络传输）。
     */
    public static byte[] toWavBytes(short[] pcmData, int sampleRate) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        int dataSize = pcmData.length * 2;
        int byteRate = sampleRate * 2;

        DataOutputStream dos = new DataOutputStream(baos);
        dos.writeBytes("RIFF");
        dos.writeInt(Integer.reverseBytes(36 + dataSize));
        dos.writeBytes("WAVE");
        dos.writeBytes("fmt ");
        dos.writeInt(Integer.reverseBytes(16));
        dos.writeShort(Short.reverseBytes((short) 1));
        dos.writeShort(Short.reverseBytes((short) 1));
        dos.writeInt(Integer.reverseBytes(sampleRate));
        dos.writeInt(Integer.reverseBytes(byteRate));
        dos.writeShort(Short.reverseBytes((short) 2));
        dos.writeShort(Short.reverseBytes((short) 16));
        dos.writeBytes("data");
        dos.writeInt(Integer.reverseBytes(dataSize));
        for (short sample : pcmData) {
            dos.writeShort(Short.reverseBytes(sample));
        }
        dos.flush();
        return baos.toByteArray();
    }
}
