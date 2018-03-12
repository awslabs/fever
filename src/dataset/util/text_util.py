import re


def is_blank(line):
    pattern = re.compile(r'\s+')
    sentence = re.sub(pattern, '', line)
    return len(sentence.strip())==0

def exact_match(search,text):
    if len(search.strip()) >0 and len (text.strip())>0:
        return len(re.findall('\\b' + re.escape(search.strip()) + '\\b', " "+text+ " ")) > 0
    return False