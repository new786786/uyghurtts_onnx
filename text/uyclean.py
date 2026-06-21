import re

# 基础数字词汇（1-9）
UYGHUR_BASE_DIGITS = {
    '0': 'نۆل',
    '1': 'بىر',
    '2': 'ئىككى',
    '3': 'ئۈچ',
    '4': 'تۆت',
    '5': 'بەش',
    '6': 'ئالتە',
    '7': 'يەتتە',
    '8': 'سەككىز',
    '9': 'توققۇز',
}

# 十位数词汇
UYGHUR_TENS = {
    '1': 'ئون',
    '2': 'يىگىرمە',
    '3': 'ئوتتۇز',
    '4': 'قىرىق',
    '5': 'ئەللىك',
    '6': 'ئاتمىش',
    '7': 'يەتمىش',
    '8': 'سەكسەن',
    '9': 'توقسان',
}

# 数量级单位（从千开始，每三位一级）
UYGHUR_SCALES = [
    (4, 'مىڭ'),       # 10^3
    (7, 'مىلىيۇن'),   # 10^6
    (10, 'مىلىيارد'), # 10^9
    (13, 'تىرلىيۇن'), # 10^12
    (16, 'تىرلىيارد'), # 10^15
]

# 序数词映射（用于个位数）
ORDINAL_MAP = {
    "بىر": "بىرىنچى",
    "ئىككى": "ئىككىنچى",
    "ئۈچ": "ئۈچىنچى",
    "تۆت": "تۆتىنچى",
    "بەش": "بەشىنچى",
    "ئالتە": "ئالتىنچى",
    "يەتتە": "يەتتىنچى",
    "سەككىز": "سەككىزىنچى",
    "توققۇز": "توققۇزىنچى",
}

# 维吾尔语月份名称
UYGHUR_MONTHS = 'ماي|ئاپرېل|مارت|فېۋرال|يانۋار|ئىيۇن|ئىيۇل|ئاۋغۇست|سېنتەبىر|ئۆكتەبىر|نويابىر|دېكابىر'


def numstr2str(numstr: str, is_ordinal: bool = False) -> str:
    """
    将整数数字字符串转换为维吾尔语文字
    :param numstr: 数字字符串（仅包含数字）
    :param is_ordinal: True返回序数词（如1->بىرىنچى），False返回基数词（如1->بىر）
    :return: 维吾尔语字符串
    """
    # 输入验证
    if not numstr.isdigit():
        raise ValueError("输入必须为数字字符串")
    if len(numstr) > 18:
        return "خانە سانى ئون سەككىزدىن يۇقىرى بولمىسۇن"
    
    # 去除前导零，但保留单个零
    original = numstr
    numstr = numstr.lstrip('0')
    if not numstr:  # 全部是零的情况
        return "نۆل"
    if numstr == "0":
        return "نۆل"
    
    result_parts = []
    length = len(numstr)
    
    for i, digit in enumerate(numstr):
        if digit == '0':
            continue
            
        pos_from_end = length - i  # 从右向左的位置（1-based）
        remainder = pos_from_end % 3
        
        # 个位或百位（余数为1或0）
        if remainder == 1 or remainder == 0:
            result_parts.append(UYGHUR_BASE_DIGITS[digit])
        
        # 十位（余数为2）
        if remainder == 2:
            result_parts.append(UYGHUR_TENS[digit])
        
        # 百位单位
        if remainder == 0:
            result_parts.append("يۈز")
        
        # 添加数量级单位（根据位置）
        for scale_pos, scale_name in UYGHUR_SCALES:
            if pos_from_end == scale_pos:
                # 检查下一个单位是否全为零
                next_start = length - scale_pos
                if next_start >= 0 and not all(ch == '0' for ch in numstr[next_start:next_start+3]):
                    result_parts.append(scale_name)
                break
    
    # 处理特殊情况：单个 "بىر يۈز" 应简化为 "يۈز"
    if len(result_parts) >= 2 and result_parts[0] == "بىر" and result_parts[1] == "يۈز":
        result_parts = result_parts[1:]  # 去掉 "بىر"
    
    result = " ".join(result_parts).strip()
    
    # 处理序数词
    if is_ordinal:
        # 对于多位数，更智能地处理序数词后缀
        # 根据最后一个词选择合适后缀
        last_word = result.split()[-1] if ' ' in result else result
        
        if last_word in ORDINAL_MAP:
            # 如果整个结果就是单个数字词
            if result == last_word:
                return ORDINAL_MAP[last_word]
            # 否则只在末尾添加ىنچى
            return f"{result} ىنچى"
        else:
            return f"{result} ىنچى"
    
    return result


def decimal_to_uyghur(num_str: str, is_ordinal: bool = False) -> str:
    """
    将小数字符串转换为维吾尔语文字
    :param num_str: 小数字符串（如 "0.68", "123.456"）
    :param is_ordinal: 是否转换为序数词（小数通常不用序数词，但为保持接口一致）
    :return: 维吾尔语字符串
    """
    if '.' not in num_str:
        return numstr2str(num_str, is_ordinal)
    
    int_part, frac_part = num_str.split('.', 1)
    
    # 处理整数部分
    if int_part == "0" or int_part == "":
        int_text = "نۆل"
    else:
        int_text = numstr2str(int_part, is_ordinal=False)
    
    # 处理小数部分（逐位转换）
    if frac_part:
        if frac_part:
            frac_digits = [UYGHUR_BASE_DIGITS[ch] for ch in frac_part if ch in UYGHUR_BASE_DIGITS]
            frac_text = " ".join(frac_digits)
        else:
            frac_text = ""
    else:
        frac_text = ""
    
    # 构建结果
    if frac_text:
        return f"{int_text} پۈتۈن نۇقتا {frac_text}"
    else:
        return int_text


def convert_numbers_in_text(text: str, convert_month_dates: bool = True) -> str:
    """
    将文本中的数字模式转换为维吾尔语文字
    """
    
    # 定义所有转换函数
    def year_replacer(match):
        num = match.group(1)
        suffix = match.group(2)
        converted = numstr2str(num, is_ordinal=True)
        # 对于年份，如果是 2026-يىللىق，应该去掉序数词的 "ىنچى" 后缀，使用 "يىللىق"
        # 实际上 -يىللىq 表示"年份的"，应该用序数词形式
        return f"{converted} {suffix}"
    
    def month_day_replacer(match):
        num = match.group(1)
        month = match.group(2)
        # 日期中的数字用基数词
        return f"{numstr2str(num, is_ordinal=False)}-{month}"
    
    def trailing_hyphen_replacer(match):
        num = match.group(1)
        # 单独的 16- 格式，转换为序数词
        return f"{numstr2str(num, is_ordinal=True)}-"
    
    def dot_replacer(match):
        num = match.group(1)
        return numstr2str(num, is_ordinal=True)
    
    def decimal_replacer(match):
        num = match.group(1)
        return decimal_to_uyghur(num, is_ordinal=False)
    
    def normal_replacer(match):
        num = match.group(1)
        return numstr2str(num, is_ordinal=False)
    
    # 保存原始文本，逐步替换
    result = text
    
    # 1. 处理年份（带 -يىلى 或 -يىللىق）
    result = re.sub(r'(\d+)-(يىلى|يىللىق)', year_replacer, result)
    
    # 2. 处理月份日期（数字-月份）
    if convert_month_dates:
        result = re.sub(r'(\d+)-(' + UYGHUR_MONTHS + r')', month_day_replacer, result)
    
    # 3. 处理小数点数字（小数）
    result = re.sub(r'(\d+\.\d+)', decimal_replacer, result)
    
    # 4. 处理单独的数字加短横线（如 16-、98-）
    # 关键：匹配数字后跟短横线，且短横线后面不是维吾尔文字母（避免匹配到年份和月份）
    result = re.sub(r'(\d+)-(?![يلىلمايئاپرېل|])', trailing_hyphen_replacer, result)
    
    # 5. 处理点号结尾的序数词
    result = re.sub(r'(\d+)\.', dot_replacer, result)
    
    # 6. 处理剩余的独立整数
    result = re.sub(r'(?<!\d)(\d+)(?![\d\.])', normal_replacer, result)
    
    return result


# ==================== 测试 ====================
if __name__ == "__main__":
    print("=" * 70)
    print("测试用例：")
    print("=" * 70)
    
    # 单独测试各种格式
    test_cases = [
        # 测试单独的 16- 格式
        ("16-", "单独的16-"),
        ("98-", "单独的98-"),
        ("123-", "单独的123-"),
        ("1-", "单独的1-"),
        
        # 测试您的完整文本
        ("2026-يىللىق «قەلبداشلىق لوڭقىسى» شىنجاڭ دەرىجىدىن تاشقىرى پۇتبول بىرلەشمە مۇسابىقىسى 16-ماي ئۈرۈمچى شەھەرلىك ئولىمپىك تەنتەربىيە مەركىزىدە باشلىنىدۇ! بىلەت باھاسى 9.9 يۈەن.", "完整文本"),
        
        # 混合测试
        ("16-ماي ۋە 16-", "混合：日期和单独短横线"),
        ("1- بىرىنچى، 2- ئىككىنچى، 3- ئۈچىنچى", "列表编号"),
        ("98-يىللىق ۋە 98-", "年份和单独短横线"),
        
        # 小数测试
        ("9.9 يۈەن", "小数"),
        ("0.68", "小数"),
    ]
    
    for test_text, description in test_cases:
        converted = convert_numbers_in_text(test_text)
        print(f"\n【{description}】")
        print(f"原始: {test_text}")
        print(f"转换: {converted}")
        print("-" * 70)