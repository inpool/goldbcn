#! /usr/bin/env python
#-*- coding: utf8 -*-

import os

DIR_PATH = os.path.dirname(__file__) 
DB_PATH = os.path.join(os.environ['HOME'], '.goldendict', 'dbcn', 'dict.db')
TEMPLATE_TXT = os.path.join(DIR_PATH, '../res/template.txt')

def lookup(word):
    word = word.strip()
    if not word.isalpha():
        try:
            result = lookup_sentence(word)
        except LookupNetException:
            return None
        return result

    import sqlite3
    db = sqlite3.connect(DB_PATH)
    result = lookup_from_db(db, word)
    if result:
        return result
    try:
        result = lookup_from_net(word)
    except LookupNetException:
        db.close()
        return None
    save_into_db(db, result)
    return result

def lookup_sentence(word):
    return lookup_from_net(word)

def lookup_from_net(word):
    word = quote_item(word)
    lookup_url = 'http://dict.youdao.com/search?q=' + word
    import urllib2
    try:
        html = urllib2.urlopen(lookup_url).read()
    except urllib2.HTTPError as e:
        raise LookupNetException(word, e,geturl())
    return result_from_html(html)

def quote_item(word):
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRST0123456789-_.~"
    if isinstance(word, unicode):
        word = word.encode('utf8')
    def quote_char(char):
        if char not in safe_chars:
            char = '%%%X' % ord(char)
        return char
    return ''.join(map(quote_char, word))

def result_from_html(s):
    from lxml.html import document_fromstring
    document = document_fromstring(s)
    phrs = document.cssselect('#phrsListTab')
    if not phrs:
        return None
    phrs = phrs[0]

    keyword = phrs.cssselect('span.keyword')[0].text.decode('utf8')
    sound = phrs.cssselect('div.baav')
    means = phrs.cssselect('div.trans-container li')

    if sound:
        import re
        sound = sound[0].text_content().strip()
        sound = ' '.join(re.split(r'\s+', sound))
    else:
        sound = ''
    means = '\n'.join(i.text for i in means)

    return keyword.encode('utf8'), sound.encode('utf8'), means.encode('utf8')

def lookup_from_db(db, word):
    pass

def save_into_db(db, result):
    return

def to_txt(result):
    ERROR_MSG = '单词未找到！'
    if not result:
        return ERROR_MSG
    template = open(TEMPLATE_TXT).read()
    return template.format(*result)

class LookupNetException(Exception):
    def __init__(self, word, url):
        self.word = wor
        self.message = 'Lookup word "%s: faild!' % word
        self.url = url

def main():
    from sys import argv, stdin
    argc = len(argv)
    word = stdin.read() if argc == 1 else argv[1]
    type_ = 'txt' if argc < 3 else argv[2]
    output = globals().get('to_%s' % type_)
    result = lookup(word)
    print output(result)

if __name__ == '__main__':
    main()
