package com.uytts.tts;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 数字 → 维吾尔语文字 转换器。
 * 完整移植自 Python 端 text/uyclean.py
 */
public class NumberConverter {

    private static final Map<Character, String> BASE_DIGITS = new HashMap<>();
    private static final Map<Character, String> TENS = new HashMap<>();

    static {
        BASE_DIGITS.put('0', "\u0646\u06C6\u0644");          // نۆل
        BASE_DIGITS.put('1', "\u0628\u0649\u0631");           // بىر
        BASE_DIGITS.put('2', "\u0626\u0649\u0643\u0643\u0649"); // ئىككى
        BASE_DIGITS.put('3', "\u0626\u06C8\u0686");           // ئۈچ
        BASE_DIGITS.put('4', "\u062A\u06C6\u062A");           // تۆت
        BASE_DIGITS.put('5', "\u0628\u06D5\u0634");           // بەش
        BASE_DIGITS.put('6', "\u0626\u0627\u0644\u062A\u06D5"); // ئالتە
        BASE_DIGITS.put('7', "\u064A\u06D5\u062A\u062A\u06D5"); // يەتتە
        BASE_DIGITS.put('8', "\u0633\u06D5\u0643\u0643\u0649\u0632"); // سەككىز
        BASE_DIGITS.put('9', "\u062A\u0648\u0642\u0642\u06C7\u0632"); // توققۇز

        TENS.put('1', "\u0626\u0648\u0646");                  // ئون
        TENS.put('2', "\u064A\u0649\u06AF\u0649\u0631\u0645\u06D5"); // يىگىرمە
        TENS.put('3', "\u0626\u0648\u062A\u062A\u06C7\u0632"); // ئوتتۇز
        TENS.put('4', "\u0642\u0649\u0631\u0649\u0642");       // قىرىق
        TENS.put('5', "\u0626\u06D5\u0644\u0644\u0649\u0643"); // ئەللىك
        TENS.put('6', "\u0626\u0627\u062A\u0645\u0649\u0634"); // ئاتمىش
        TENS.put('7', "\u064A\u06D5\u062A\u0645\u0649\u0634"); // يەتمىش
        TENS.put('8', "\u0633\u06D5\u0643\u0633\u06D5\u0646"); // سەكسەن
        TENS.put('9', "\u062A\u0648\u0642\u0633\u0627\u0646"); // توقسان
    }

    private static final String HUNDRED = "\u064A\u06C8\u0632"; // يۈز
    private static final String BIR = "\u0628\u0649\u0631";     // بىر

    private static final int[][] SCALES = {
            {4,  0}, // 10^3  مىڭ
            {7,  1}, // 10^6  مىلىيۇن
            {10, 2}, // 10^9  مىلىيارد
            {13, 3}, // 10^12 تىرلىيۇن
            {16, 4}, // 10^15 تىرلىيارد
    };
    private static final String[] SCALE_NAMES = {
            "\u0645\u0649\u06AD",                              // مىڭ
            "\u0645\u0649\u0644\u0649\u064A\u06C7\u0646",       // مىلىيۇن
            "\u0645\u0649\u0644\u0649\u064A\u0627\u0631\u062F", // مىلىيارد
            "\u062A\u0649\u0631\u0644\u0649\u064A\u06C7\u0646", // تىرلىيۇن
            "\u062A\u0649\u0631\u0644\u0649\u064A\u0627\u0631\u062F", // تىرلىيارد
    };

    private static final String ORDINAL_SUFFIX = " \u0649\u0646\u0686\u0649"; // ىنچى
    private static final String POINT_WORD =
            " \u067E\u06C8\u062A\u06C8\u0646 \u0646\u06C7\u0642\u062A\u0627 "; // پۈتۈن نۇقتا

    /**
     * 整数字符串 → 维吾尔语。
     */
    public static String numToUyghur(String numStr, boolean ordinal) {
        if (numStr.isEmpty()) return "";
        numStr = numStr.replaceFirst("^0+", "");
        if (numStr.isEmpty()) return BASE_DIGITS.get('0');

        List<String> parts = new ArrayList<>();
        int len = numStr.length();

        for (int i = 0; i < len; i++) {
            char digit = numStr.charAt(i);
            if (digit == '0') continue;

            int posFromEnd = len - i;
            int remainder = posFromEnd % 3;

            if (remainder == 1 || remainder == 0) {
                parts.add(BASE_DIGITS.get(digit));
            }
            if (remainder == 2) {
                parts.add(TENS.get(digit));
            }
            if (remainder == 0) {
                parts.add(HUNDRED);
            }

            for (int[] scale : SCALES) {
                if (posFromEnd == scale[0]) {
                    int nextStart = len - scale[0];
                    boolean allZero = true;
                    if (nextStart >= 0) {
                        for (int k = nextStart; k < Math.min(nextStart + 3, len); k++) {
                            if (numStr.charAt(k) != '0') { allZero = false; break; }
                        }
                    }
                    if (!allZero) {
                        parts.add(SCALE_NAMES[scale[1]]);
                    }
                    break;
                }
            }
        }

        if (parts.size() >= 2 && parts.get(0).equals(BIR) && parts.get(1).equals(HUNDRED)) {
            parts.remove(0);
        }

        String result = join(parts, " ");
        if (ordinal) {
            result += ORDINAL_SUFFIX;
        }
        return result;
    }

    /**
     * 小数字符串 → 维吾尔语。
     */
    public static String decimalToUyghur(String numStr) {
        if (!numStr.contains(".")) return numToUyghur(numStr, false);
        String[] halves = numStr.split("\\.", 2);

        String intPart = (halves[0].isEmpty() || halves[0].equals("0"))
                ? BASE_DIGITS.get('0')
                : numToUyghur(halves[0], false);

        StringBuilder frac = new StringBuilder();
        for (char ch : halves[1].toCharArray()) {
            String w = BASE_DIGITS.get(ch);
            if (w != null) {
                if (frac.length() > 0) frac.append(" ");
                frac.append(w);
            }
        }
        if (frac.length() > 0) {
            return intPart + POINT_WORD + frac;
        }
        return intPart;
    }

    /**
     * 将文本中所有数字模式替换为维吾尔语文字。
     * 支持：年份(-يىلى)、月份日期、小数、序列编号、普通整数。
     */
    public static String convertNumbersInText(String text) {
        // 1. 年份 (-يىلى / -يىللىق)
        text = replaceAll(text,
                "(\\d+)-(\u064A\u0649\u0644\u0649|\u064A\u0649\u0644\u0644\u0649\u0642)",
                m -> numToUyghur(m.group(1), true) + " " + m.group(2));

        // 2. 小数
        text = replaceAll(text, "(\\d+\\.\\d+)",
                m -> decimalToUyghur(m.group(1)));

        // 3. 序号 (数字.)
        text = replaceAll(text, "(\\d+)\\.",
                m -> numToUyghur(m.group(1), true));

        // 4. 剩余独立整数
        text = replaceAll(text, "(?<!\\d)(\\d+)(?![\\d.])",
                m -> numToUyghur(m.group(1), false));

        return text;
    }

    // ---- 工具方法 ----

    private static String join(List<String> parts, String sep) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < parts.size(); i++) {
            if (i > 0) sb.append(sep);
            sb.append(parts.get(i));
        }
        return sb.toString();
    }

    private interface MatchReplacer {
        String replace(Matcher m);
    }

    private static String replaceAll(String input, String regex, MatchReplacer replacer) {
        Pattern p = Pattern.compile(regex);
        Matcher m = p.matcher(input);
        StringBuffer sb = new StringBuffer();
        while (m.find()) {
            m.appendReplacement(sb, Matcher.quoteReplacement(replacer.replace(m)));
        }
        m.appendTail(sb);
        return sb.toString();
    }
}
