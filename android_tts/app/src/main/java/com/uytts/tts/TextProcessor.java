package com.uytts.tts;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 维吾尔语文本 → 序列 ID 转换器。
 * 完整移植自 Python 端 text/symbols.py + text/__init__.py
 */
public class TextProcessor {

    private static final String PAD = "_";
    private static final String PUNCTUATION = ";:,.!?¡¿—…\"«»\u201C\u201D ";
    private static final String LETTERS =
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" +
            "\u0626\u0628\u067E\u062A\u062C\u0686\u062E\u062F\u0631\u0632\u0698" +
            "\u0633\u0634\u0639\u063A\u0641\u0642\u0643\u06AD\u06AF\u0644\u0645" +
            "\u0646\u06BE\u06D5\u0648\u06C6\u06C7\u06C8\u06CB\u0649\u064A\u06D0\u0627";
    private static final String LETTERS_IPA =
            "\u0251\u0250\u0252\u00E6\u0253\u0299\u03B2\u0254\u0255\u00E7\u0257\u0256" +
            "\u00F0\u02A4\u0259\u0258\u025A\u025B\u025C\u025D\u025E\u025F\u0284\u0261" +
            "\u0260\u0262\u029B\u0266\u0267\u0127\u0265\u029C\u0268\u026A\u029D\u026D" +
            "\u026C\u026B\u026E\u029F\u0271\u026F\u0270\u014B\u0273\u0272\u0274\u00F8" +
            "\u0275\u0278\u03B8\u0153\u0276\u0298\u0279\u027A\u027E\u027B\u0280\u0281" +
            "\u027D\u0282\u0283\u0288\u02A7\u0289\u028A\u028B\u2C71\u028C\u0263\u0264" +
            "\u028D\u03C7\u028E\u028F\u0291\u0290\u0292\u0294\u02A1\u0295\u02A2\u01C0" +
            "\u01C1\u01C2\u01C3\u02C8\u02CC\u02D0\u02D1\u02BC\u02B4\u02B0\u02B1\u02B2" +
            "\u02B7\u02E0\u02E4\u02DE\u2193\u2191\u2192\u2197\u2198\u0027\u0329\u0027" +
            "\u1D7B";

    private final Map<Character, Integer> symbolToId;
    private final int blankId = 0; // PAD '_' 的 ID

    public TextProcessor() {
        String allSymbols = PAD + PUNCTUATION + LETTERS + LETTERS_IPA;
        symbolToId = new HashMap<>(allSymbols.length());
        for (int i = 0; i < allSymbols.length(); i++) {
            symbolToId.put(allSymbols.charAt(i), i);
        }
    }

    /**
     * 将维吾尔语文本转换为模型输入 ID 序列（含 intersperse）。
     */
    public int[] textToSequence(String text) {
        String cleaned = basicCleaners(text);
        List<Integer> rawIds = new ArrayList<>();
        for (int i = 0; i < cleaned.length(); i++) {
            char ch = cleaned.charAt(i);
            Integer id = symbolToId.get(ch);
            if (id != null) {
                rawIds.add(id);
            }
        }
        return intersperse(rawIds, blankId);
    }

    /**
     * 获取符号表大小（供外部调试用）。
     */
    public int getVocabSize() {
        return symbolToId.size();
    }

    private String basicCleaners(String text) {
        text = text.toLowerCase();
        text = text.replaceAll("\\s+", " ");
        return text;
    }

    /**
     * 在每个 token 之间插入 blank（与 Python 端 intersperse 完全一致）。
     * 输入 [a, b, c] → 输出 [0, a, 0, b, 0, c, 0]
     */
    private int[] intersperse(List<Integer> ids, int blankItem) {
        int[] result = new int[ids.size() * 2 + 1];
        for (int i = 0; i < result.length; i++) {
            result[i] = blankItem;
        }
        for (int i = 0; i < ids.size(); i++) {
            result[i * 2 + 1] = ids.get(i);
        }
        return result;
    }
}
