# -*- coding: utf-8 -*-

import os
import urllib2
import sqlite3

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.expanduser('~/.goldendict/dbcn/dict.db')
TEMPLATE_TXT = os.path.join(DIR_PATH, 'res/template.txt')


def get_db():
    if hasattr(get_db, 'db'):
        return get_db.db

    db = sqlite3.connect(DB_PATH)  # @UndefinedVariable

    get_db.db = db
    return db


def lookup(word):
    word = word.strip()
    if not word.isalpha():
        try:
            result = lookup_from_net(word)
        except LookupNetException:
            return None
        return result

    result = lookup_from_db(word)
    if result:
        return result
    result = lookup_from_net(word)
    save_into_db(result)
    return result


def lookup_from_net(word):
    try:
        html = xml_from_net(word)
    except LookupNetException:
        return None
    return result_from_xml(html)


def lookup_from_db(word):
    db = get_db()
    cursor = db.cursor()
    word = word.lower()
    table_name = get_table_name(word)
    sql = 'SELECT keyword, sound, mean FROM %s where word=?' % table_name
    result = cursor.execute(sql, (word,)).fetchone()
    if result:
        return tuple(i.encode('utf-8') for i in result)


def xml_from_net(word, lookup_url=None):
    word = quote_item(word)
    if lookup_url is None:
        lookup_url = ('http://dict.youdao.com/fsearch?q=%s&doctype=xml'
                      '&xmlVersion=3.2&le=eng&pos=-1')
    lookup_url = lookup_url % word
    try:
        xml = urllib2.urlopen(lookup_url).read()
    except urllib2.HTTPError as e:
        raise LookupNetException(word, e, lookup_url)
    return xml


def quote_item(word):
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRST0123456789-_.~"
    if isinstance(word, unicode):
        word = word.encode('utf8')

    def quote_char(char):
        if char not in safe_chars:
            char = '%%%X' % ord(char)
        return char
    return ''.join(map(quote_char, word))


def result_from_xml(s):
    from xml.etree import ElementTree
    et = ElementTree.fromstring(s)
    means_els = et.findall('./custom-translation/translation/content')
    if not means_els:
        web_path = "./yodao-web-dict/web-translation[@same='true']/trans/value"
        means_els = et.findall(web_path)
        if not means_els:
            return
    means = '\n'.join(e.text.strip().encode('utf-8') for e in means_els)
    keyword = et.find('./return-phrase').text.strip().encode('utf-8')
    uk_sound = et.find('./uk-phonetic-symbol')
    us_sound = et.find('./us-phonetic-symbol')
    sounds = []
    if uk_sound is not None:
        sounds.append('英 [%s] ' % uk_sound.text.strip().encode('utf-8'))
    if us_sound is not None:
        sounds.append('美 [%s] ' % us_sound.text.strip().encode('utf-8'))
    sound = ''.join(sounds)
    return keyword, sound, means


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
        self.word = word
        self.message = 'Lookup word "%s: faild!' % word
        self.url = url
