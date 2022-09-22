textarea_slt = "body > div.c970 > div.con_wen > div:nth-child(3) > div.con_pl > textarea"
import logging
import re
from time import sleep
import requests

class WordMatcher:
    def __init__(self, regex, context_expand = 8, exclude_chars = '\t\r\n') -> None:
        self.regex = regex
        self.context_expand = context_expand
        self.exclude_chars = exclude_chars
        pass

    def get_all_context(self, text):
        if text is None:
            return None
        context_list = list()
        all_matches = re.finditer(self.regex, text)
        text_length = len(text)
        for match_elem in all_matches:
            context = text[max(match_elem.start()-self.context_expand, 0):min(match_elem.end()+self.context_expand, text_length)]
            if self.exclude_chars is not None:
                for ch in self.exclude_chars:
                    context = context.replace(ch, "")
            context_list.append(context)
        return context_list
    
    def get_n_context(self, text, n=1):
        if text is None:
            return None
        context_list = list()
        all_matches = re.finditer(self.regex, text)
        text_length = len(text)
        cnt = 0
        for match_elem in all_matches:
            context = text[max(match_elem.start()-self.context_expand, 0):min(match_elem.end()+self.context_expand, text_length)]
            if self.exclude_chars is not None:
                for ch in self.exclude_chars:
                    context = context.replace(ch, "")
            context_list.append(context)
            cnt += 1
            if cnt >= n:
                break
        return context_list

def get_keyword_regex(word_list):
    res = list()
    if not word_list:
        raise ValueError
    for word in word_list:
        if not word:
            continue
        res.append(f"{word}|")

    return "".join(res)[:-1]

# class multipleConditionMatcher:
#     def __init__(self, context_matcher_list) -> None:
#         self.context_matcher_list = context_matcher_list

#     def match(self, text):
#         for matcher in self.context_matcher_list:
#             if matcher


def is_ok_status(url, logger = logging.getLogger()):
    res = requests.get(url)
    if str(res.status_code)[0] == '2':
        logger.warning(f"Access granted. Resume")
        return True
    if str(res.status_code)[0] == '4':
        logger.warning(f"Access denied. sleeping")
        sleep(600)
        return False
    else:
        logger.warning(f"More operation might be needed")
        sleep(10)
        return True

if __name__ == "__main__":
    word_list = [
    "起火",
    "火灾",
    "燃烧",
    "闪燃",
    "着火",
    "自燃",
    "爆燃",
    "爆炸",
    "溢油",
    "渗漏",
    "泄漏",
    "外漏",
    "外溢",
    "外泄",
    ]
    regex = get_keyword_regex(word_list)
    matcher = WordMatcher(regex)
    text = "random"
    print(matcher.get_all_context(text))