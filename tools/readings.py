"""Adds search readings to Data/almanac.json (run after build.js; Python 3.11 with sudachipy + sudachidict_full).

  py -3.11 readings.py

Two kinds of reading, because the game's names mix real words with coined ones:
  - "kana" per item: Sudachi's reading of each searchable string (name, zone, fishing spot, gathered items), which gets
    real words and ateji right (明けの旗魚 -> アケノカジキ) but guesses at coined compounds (輝金鉱 -> アキラキンコウ).
  - "kanji" at the top: every kanji's on and kun readings from Unicode's Unihan database, so the app can match a query
    against any reading of each kanji (輝金鉱 -> キ/キン/コン/コウ...), which coined compounds need.
Both are katakana. SudachiDict is Apache-2.0; Unihan is under the Unicode License v3 (notices in THIRD-PARTY-almanac.txt).
"""
import json, os, re, unicodedata
from sudachipy import Dictionary, SplitMode

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.environ.get('ALMANAC_OUT') or os.path.join(HERE, '..', '..', 'Data'), 'almanac.json')
UNIHAN = os.path.join(HERE, 'cache', 'Unihan_Readings.txt')

def is_kanji(c):
    return '一' <= c <= '鿿' or c in '々〆'

# ---- romaji (Unihan's Hepburn) -> katakana
TABLE = {}
for row in '''a ア i イ u ウ e エ o オ
ka カ ki キ ku ク ke ケ ko コ kya キャ kyu キュ kyo キョ
ga ガ gi ギ gu グ ge ゲ go ゴ gya ギャ gyu ギュ gyo ギョ
sa サ shi シ su ス se セ so ソ sha シャ shu シュ sho ショ
za ザ ji ジ zu ズ ze ゼ zo ゾ ja ジャ ju ジュ jo ジョ
ta タ chi チ tsu ツ te テ to ト cha チャ chu チュ cho チョ
da ダ di ヂ du ヅ de デ do ド
na ナ ni ニ nu ヌ ne ネ no ノ nya ニャ nyu ニュ nyo ニョ
ha ハ hi ヒ fu フ he ヘ ho ホ hya ヒャ hyu ヒュ hyo ヒョ
ba バ bi ビ bu ブ be ベ bo ボ bya ビャ byu ビュ byo ビョ
pa パ pi ピ pu プ pe ペ po ポ pya ピャ pyu ピュ pyo ピョ
ma マ mi ミ mu ム me メ mo モ mya ミャ myu ミュ myo ミョ
ya ヤ yu ユ yo ヨ
ra ラ ri リ ru ル re レ ro ロ rya リャ ryu リュ ryo リョ
wa ワ wo ヲ'''.split('\n'):
    parts = row.split()
    for r, k in zip(parts[::2], parts[1::2]):
        TABLE[r] = k

def kata(romaji):
    s, out, i = romaji.lower(), '', 0
    while i < len(s):
        if s[i] == 'n' and (i + 1 == len(s) or s[i + 1] not in 'aiueoy'):
            out += 'ン'; i += 1; continue
        if i + 1 < len(s) and s[i] == s[i + 1] and s[i] not in 'aiueon':
            out += 'ッ'; i += 1; continue
        for n in (3, 2, 1):
            if s[i:i + n] in TABLE:
                out += TABLE[s[i:i + n]]; i += n; break
        else:
            return None  # unexpected spelling: skip this reading
    return out

def unihan_readings(chars):
    on, kun = {}, {}
    with open(UNIHAN, encoding='utf-8') as f:
        for line in f:
            m = re.match(r'U\+([0-9A-F]+)\tkJapanese(On|Kun)\t(.+)', line)
            if not m: continue
            c = chr(int(m.group(1), 16))
            if c not in chars: continue
            target = on if m.group(2) == 'On' else kun
            for r in m.group(3).split():
                k = kata(r)
                if k: target.setdefault(c, []).append(k)
    return {c: {'on': sorted(set(on.get(c, []))), 'kun': sorted(set(kun.get(c, [])))} for c in chars if c in on or c in kun}

def to_kata(s):
    return ''.join(chr(ord(c) + 0x60) if 'ぁ' <= c <= 'ゖ' else c for c in unicodedata.normalize('NFKC', s))

def main():
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    tok = Dictionary(dict='full').create()  # noqa: deprecated alias, kept for older SudachiPy
    reading = lambda s: ''.join(m.reading_form() for m in tok.tokenize(s, SplitMode.C))

    chars = set()
    for item in data['items']:
        zone = data['terr'][str(item['terr'])]['name'] if 'terr' in item and str(item.get('terr')) in data['terr'] else item.get('zone', '')
        strings = [item['name'], zone, item.get('spot', '')] + item.get('items', [])
        kana = []
        for s in strings:
            if not s or not any(is_kanji(c) for c in s): continue
            chars.update(c for c in s if is_kanji(c))
            r = to_kata(reading(s))
            if r and r not in kana: kana.append(r)
        if kana: item['kana'] = kana
        else: item.pop('kana', None)
    for t in data['terr'].values():
        chars.update(c for c in t['name'] if is_kanji(c))

    data['kanji'] = unihan_readings(chars)
    data['meta']['sources'] = [s for s in data['meta']['sources'] if 'Sudachi' not in s and 'Unihan' not in s] + \
        ['SudachiDict (WorksApplications, Apache-2.0) via SudachiPy: readings', 'Unicode Unihan database (Unicode License v3): kanji readings']
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    notice = os.path.join(os.path.dirname(DATA), 'THIRD-PARTY-almanac.txt')
    with open(notice, encoding='utf-8') as f:
        text = f.read().split('\n=== SudachiDict')[0].rstrip('\n')
    with open(os.path.join(HERE, 'cache', 'unicode_license.txt'), encoding='utf-8') as f:
        unicode_license = f.read().strip()
    text += ('\n\n=== SudachiDict (https://github.com/WorksApplications/SudachiDict) — readings for search ===\n'
             'Copyright (c) 2017-2023 Works Applications Co., Ltd.\nLicensed under the Apache License, Version 2.0 '
             '(http://www.apache.org/licenses/LICENSE-2.0).\n\n'
             '=== Unicode Unihan database (https://www.unicode.org/charts/unihan.html) — kanji readings ===\n'
             + unicode_license + '\n')
    with open(notice, 'w', encoding='utf-8') as f:
        f.write(text)

    with_kana = sum(1 for i in data['items'] if 'kana' in i)
    missing = sorted(c for c in chars if c not in data['kanji'])
    print(f"{with_kana} items with readings, {len(data['kanji'])} kanji, missing: {''.join(missing) or 'none'}")

if __name__ == '__main__':
    main()
