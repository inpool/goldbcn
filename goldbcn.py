#-*- coding: utf-8 -*-

import os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.expanduser('~/.goldendict/dbcn/dict.db')
TEMPLATE_TXT = os.path.join(DIR_PATH, 'res/template.txt')


def get_db():
    if hasattr(get_db, 'db'):
        return get_db.db
    import sqlite3
    db = sqlite3.connect(DB_PATH)
    get_db.db = db
    return db

def lookup(word):
    word = word.strip()
    if not word.isalpha():
        try:
            result = lookup_sentence(word)
        except LookupNetException:
            return None
        return result

    result = lookup_from_db(word)
    if result:
        return result
    try:
        html = response_from_net(word)
    except LookupNetException:
        db.close()
        return None
    result = result_from_html(html)
    save_into_db(result)
    return result

def lookup_sentence(word):
    try:
        html = response_from_net(word)
    except LookupNetException:
        return None
    return result_from_html(html)

def lookup_from_db(word):
    db = get_db()
    cursor = db.cursor()
    word = word.lower()
    table_name = get_table_name(word)
    sql = 'SELECT keyword, sound, mean FROM %s where word=?' % table_name
    result = cursor.execute(sql, (word,)).fetchone()
    if result:
        return tuple(i.encode('utf-8') for i in result)

def response_from_net(word):
    word = quote_item(word)
    lookup_url = 'http://dict.youdao.com/search?q=' + word
    import urllib2
    try:
        html = urllib2.urlopen(lookup_url).read()
    except urllib2.HTTPError as e:
        raise LookupNetException(word, e,geturl())
    return html

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
    means = [i.text for i in means]
    while None in means:
        means.remove(None)
    means = '\n'.join(means).strip()

    return keyword.encode('utf8'), sound.encode('utf8'), means.encode('utf8')

def save_into_db(result):
    word, sound, mean = [i.decode('utf-8') for i in result]
    if not mean:
        return
    word = word.lower()
    table_name = get_table_name(word)
    sql = 'SELECT 1 FROM %s WHERE word=?' % table_name
    db = get_db()
    cursor = db.cursor()
    if cursor.execute(sql, (word, )).fetchone():
        return
    sql = 'INSERT INTO %s (word, keyword, sound, mean) VALUES (?, ?, ?, ?)'
    cursor.execute(sql % table_name, (word.lower(), word, sound, mean))
    db.commit()

def get_table_name(word):
    word = word.lower()
    return 'word_%s' % (word[0] + word[-1])

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
