# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
import os
import zlib
import sys
from importlib import import_module
import dbm  # @UnresolvedImport

PY2 = sys.version_info.major == 2
PY3 = sys.version_info.major == 3

if PY2:
    request = import_module('urllib2')
    dbmerror = dbm.error
else:
    request = import_module('urllib.request')
    dbmerror = import_module('_dbm').error

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.expanduser('~/.goldendict/dbcn/dict')
TEMPLATE_TXT = os.path.join(DIR_PATH, 'res/template.txt')
ERROR_REASON = {13: '权限不足，请确定您有适当的读取或写入权限',
                22: '文件类型或格式错误'}


def get_db(flag='r'):
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH)
    error_fmt = '数据库打开失败： %s！'
    try:
        db = dbm.open(DB_PATH, flag)
    except:
        try:
            db = dbm.open(DB_PATH, 'c')
        except dbmerror as e:
            eno = e.args[0]
            estr = e.args[1]
            errmsg = error_fmt % ERROR_REASON.get(eno, estr)
            if PY2:
                errmsg = errmsg.encode('utf-8')
            print(errmsg, file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            errmsg = error_fmt % e.args[0]
            if PY2:
                errmsg = errmsg.encode('utf-8')
            print(errmsg, file=sys.stderr)
            sys.exit(1)
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
    if result is not None:
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
    word = word.lower()
    if word in db:
        result = zlib.decompress(db[word]).decode('utf-8').split('\n', 2)
    else:
        result = None

    db.close()
    return result


def xml_from_net(word, lookup_url=None):
    word = request.quote(word)
    if lookup_url is None:
        lookup_url = ('http://dict.youdao.com/fsearch?q=%s&doctype=xml'
                      '&xmlVersion=3.2&le=eng&pos=-1')
    lookup_url = lookup_url % word
    try:
        req = request.urlopen(lookup_url)
    except request.HTTPError as e:
        raise LookupNetException(word, e, lookup_url)
    xml = req.read()
    req.close()
    return xml


def result_from_xml(s):
    from xml.etree import ElementTree
    et = ElementTree.fromstring(s)
    means_els = et.findall('./custom-translation/translation/content')
    if not means_els:
        web_path = "./yodao-web-dict/web-translation[@same='true']/trans/value"
        means_els = et.findall(web_path)
        if not means_els:
            return
    means = '\n'.join(e.text.strip() for e in means_els)
    keyword = et.find('./return-phrase').text.strip()
    uk_sound = et.find('./uk-phonetic-symbol')
    us_sound = et.find('./us-phonetic-symbol')
    sounds = []
    if uk_sound is not None:
        sounds.append('英 [%s] ' % uk_sound.text.strip())
    if us_sound is not None:
        sounds.append('美 [%s] ' % us_sound.text.strip())
    sound = ''.join(sounds)
    return keyword, sound, means


def save_into_db(result):
    word, sound, mean = result  # @UnusedVariable
    if not mean:
        return
    key = word.lower().encode('utf-8')
    val = zlib.compress('\n'.join(result).encode('utf-8'))
    db = get_db('w')
    db[key] = val
    db.close()


def to_txt(result):
    ERROR_MSG = '单词未找到！'
    if not result:
        return ERROR_MSG
    result = [i for i in result]
    template = open(TEMPLATE_TXT, 'rb').read()
    template = template.decode('utf-8')
    return template.format(*result)


class LookupNetException(Exception):

    def __init__(self, word, url):
        self.word = word
        self.message = 'Lookup word "%s: faild!' % word
        self.url = url
