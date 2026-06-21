'''
Defines the set of symbols used in text input to the model.
Auto-generated from dataset: 60k.txt
'''

# Uyghur (basic_cleaners)
_pad        = '_'

# 停顿/标点符号（按语义分组）
# 短停顿: ، ,
# 长停顿: .  。
# 疑问停顿: ؟ ?
# 强调停顿: !
# 延长停顿: …
# 连接停顿: - — –
# 中停顿: : ؛ ;
_punctuation = '!,-.:،؛؟–—()_«¬»“”•‹›− '

_letters = 'ئابتجخدرزسشغـفقكلمنوىيپچژکڭگھۆۇۈۋیېە'

# Export all symbols:
symbols = [_pad] + list(_punctuation) + list(_letters)

# Special symbol ids
SPACE_ID = symbols.index(" ")
