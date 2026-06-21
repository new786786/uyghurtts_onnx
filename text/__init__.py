""" from https://github.com/keithito/tacotron """
import re
from unidecode import unidecode
from text.symbols import symbols
_whitespace_re = re.compile(r'\s+')
_symbol_to_id = {s: i for i, s in enumerate(symbols)}
_id_to_symbol = {i: s for i, s in enumerate(symbols)}
def text_to_sequence(text, cleaner_names):
  sequence = []
  clean_text = basic_cleaners(text)
  for symbol in clean_text:
    if symbol not in _symbol_to_id.keys():
      continue
    symbol_id = _symbol_to_id[symbol]
    sequence += [symbol_id]
  return sequence

def cleaned_text_to_sequence(cleaned_text):
  sequence = [_symbol_to_id[symbol] for symbol in cleaned_text if symbol in _symbol_to_id.keys()]
  return sequence
def sequence_to_text(sequence):
  result = ''
  for symbol_id in sequence:
    s = _id_to_symbol[symbol_id]
    result += s
  return result
def expand_abbreviations(text):
  for regex, replacement in _abbreviations:
    text = re.sub(regex, replacement, text)
  return text
def collapse_whitespace(text):
    return re.sub(_whitespace_re, ' ', text)
def convert_to_ascii(text):
    return unidecode(text)
def basic_cleaners(text):
    text = text.lower()
    text = collapse_whitespace(text)
    return text
