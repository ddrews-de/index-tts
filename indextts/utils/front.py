# -*- coding: utf-8 -*-
import traceback
import re

class TextNormalizer:
    def __init__(self):
        # self.normalizer = Normalizer(cache_dir="textprocessing/tn")
        self.zh_normalizer = None
        self.en_normalizer = None
        self.char_rep_map = {
            "：": ",",
            "；": ",",
            ";": ",",
            "，": ",",
            "。": ".",
            "！": "!",
            "？": "?",
            "\n": ".",
            "·": ",",
            "、": ",",
            "...": "…",
            "……": "…",
            "$": ".",
            "“": "'",
            "”": "'",
            '"': "'",
            "‘": "'",
            "’": "'",
            "（": "'",
            "）": "'",
            "(": "'",
            ")": "'",
            "《": "'",
            "》": "'",
            "【": "'",
            "】": "'",
            "[": "'",
            "]": "'",
            "—": "-",
            "～": "-",
            "~": "-",
            "「": "'",
            "」": "'",
            ":": ",",
        }

    def match_email(self, email):
        # Regular expression match mailbox format: numeric English @ numeric English.English
        pattern = r'^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z]+$'
        return re.match(pattern, email) is not None

    def use_chinese(self, s):
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', s))
        has_digit = bool(re.search(r'\d', s))
        has_alpha = bool(re.search(r'[a-zA-Z]', s))
        is_email = self.match_email(s)
        if has_chinese or not has_alpha or is_email:
            return True
        else:
            return False

    def load(self):
        # print(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        # sys.path.append(model_dir)
        import platform
        if platform.system() == "Darwin":
            from wetext import Normalizer
            self.zh_normalizer = Normalizer(remove_erhua=False,lang="zh",operator="tn")
            self.en_normalizer = Normalizer(lang="en",operator="tn")
        else:
            from tn.chinese.normalizer import Normalizer as NormalizerZh
            from tn.english.normalizer import Normalizer as NormalizerEn
            self.zh_normalizer = NormalizerZh(remove_interjections=False, remove_erhua=False,overwrite_cache=False)
            self.en_normalizer = NormalizerEn(overwrite_cache=False)

    def infer(self, text):
        pattern = re.compile("|".join(re.escape(p) for p in self.char_rep_map.keys()))
        replaced_text = pattern.sub(lambda x: self.char_rep_map[x.group()], text)
        if not self.zh_normalizer or not self.en_normalizer:
            print("Error, text normalizer is not initialized !!!")
            return ""
        try:
            normalizer = self.zh_normalizer if self.use_chinese(replaced_text) else self.en_normalizer
            result = normalizer.normalize(replaced_text)
        except Exception:
            result = ""
            print(traceback.format_exc())
        result = self.restore_pinyin_tone_numbers(replaced_text, result)
        return result

    def pinyin_match(self, pinyin):
        pattern = r"(qun)(\d)"
        repl = r"qvn\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(quan)(\d)"
        repl = r"qvan\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(que)(\d)"
        repl = r"qve\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(qu)(\d)"
        repl = r"qv\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(ju)(\d)"
        repl = r"jv\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(jue)(\d)"
        repl = r"jve\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(xun)(\d)"
        repl = r"xvn\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(xue)(\d)"
        repl = r"xve\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(xu)(\d)"
        repl = r"xv\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(juan)(\d)"
        repl = r"jvan\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(jun)(\d)"
        repl = r"jvn\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)

        pattern = r"(xuan)(\d)"
        repl = r"xvan\g<2>"
        pinyin = re.sub(pattern, repl, pinyin)
        return pinyin

    def restore_pinyin_tone_numbers(self,original_text, processed_text):
        # Step 1: Recovering tone numbers after pinyin (1-4)
        # Create a mapping of Chinese numerals to Arabic numerals
        chinese_to_num = {'一': '1', '二': '2', '三': '3', '四': '4'}

        # Use regular expressions to find combinations of pinyin + Chinese numerals (e.g. "xuan si")
        def replace_tone(match):
            pinyin = match.group(1)  # phonetic component
            chinese_num = match.group(2)  # Chinese numerals section
            # Conversion of Chinese numerals to Arabic numerals
            num = chinese_to_num.get(chinese_num, chinese_num)
            return f"{pinyin}{num}"

        # Match Pinyin followed by Chinese numerals (1, 2, 3, 4)
        pattern = r'([a-zA-Z]+)([一二三四])'
        restored_text = re.sub(pattern, replace_tone, processed_text)
        restored_text = restored_text.lower()
        restored_text = self.pinyin_match(restored_text)

        return restored_text


if __name__ == '__main__':
    # test program
    text_normalizer = TextNormalizer()
    print(text_normalizer.infer("2.5平方电线"))
