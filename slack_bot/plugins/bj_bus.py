# coding=utf-8
import os
import urllib2
import hashlib
from datetime import date
import cPickle as pickle

import lxml.etree as ET

from utils import timestamp2str

description = """
北京公交信息, 触发条件: "公交 路数 [当前所在第几站] [私聊]", 比如：
* 公交 571
* 公交 571 18
"""

URL1 = u'/aiguang/bjgj.c?m=checkUpdate&version=1'
URL2 = u'/aiguang/bjgj.c?m=update&id={0}'
URL3 = (u'/bus.php?city=%E5%8C%97%E4%BA%AC&id={0}'
        u'&no={1}&type={2}&encrypt={3}&versionid=2')
URL4 = u'http://bjgj.aibang.com:8899'


# https://github.com/andelf/beijing-realtime-bus/blob/master/bjgj.py
class Cipher(object):
    __doc__ = u'encrypt & decrypt base64 data'

    def __init__(self, key):
        self.key = str(key)

    @staticmethod
    def new_from_key(key):
        return Cipher((u'aibang' + str(key)))

    def _make_translate_table(self):
        key_bytes = bytearray(hashlib.md5(self.key).hexdigest(), u'utf-8')
        ret_val = list(range(256L))
        k = 0L
        m = 0L
        for i in range(256L):
            k = (255L & ((k + key_bytes[m]) + ret_val[i]))
            [ret_val[i], ret_val[k]] = [ret_val[k], ret_val[i]]
            m = ((1L + m) % len(key_bytes))
        return ret_val

    def translate(self, raw):
        trans_table = self._make_translate_table()
        raw_bytes = bytearray(raw)
        ret_val = bytearray(len(raw_bytes))
        j = 0L
        k = 0L
        for i in range(len(raw_bytes)):
            k = (255L & (k + 1L))
            j = (255L & (j + trans_table[k]))
            [trans_table[j], trans_table[k]] = [trans_table[k], trans_table[j]]
            n = (255L & (trans_table[k] + trans_table[j]))
            ret_val[i] = (raw_bytes[i] ^ trans_table[n])
        return str(ret_val)

    def decrypt(self, cipher_text):
        return self.translate(cipher_text.decode(u'base64')) if cipher_text else ''

    def encrypt(self, plain_text):
        return self.translate(plain_text).encode(u'base64')


def decrypt_busline_etree(et):
    busline = xpath_etree_children_to_dict_list(u'//busline', et)[0L]
    stations = xpath_etree_children_to_dict_list(
        u'//busline/stations/station', et)
    cipher = Cipher.new_from_key(busline[u'lineid'])
    busline = dict(
        *[busline],
        **{k: cipher.decrypt(v).decode(u'utf-8')
            for (k, v) in busline.items()
            if (k in [u'shotname', u'coord', u'linename'])}
    )

    def _hy_anon_fn_9():
        f_1236 = (lambda it: {k: cipher.decrypt(v).decode(
            u'utf-8', u'ignore') for (k, v) in it.items()})
        for v_1235 in stations:
            yield f_1236(v_1235)

    stations = list(_hy_anon_fn_9())
    busline[u'stations'] = stations
    return busline


def decrypt_bus_realtime_info(bus):
    cipher = Cipher.new_from_key(bus[u'gt'])
    return dict(
        *[bus],
        **{k: cipher.decrypt(v).decode(u'utf-8')
            for (k, v) in bus.items()
            if (k in [u'ns', u'nsn', u'sd',
                      u'srt', u'st', u'x', u'y'])}
    )


def etree_xpath_children_to_dict_list(et, path):
    return xpath_etree_children_to_dict_list(path, et)


def xpath_etree_children_to_dict_list(path, et):
    def _hy_anon_fn_15():
        f_1238 = (
            lambda it: {elem.tag: elem.text for elem in it.getchildren()})
        for v_1237 in et.xpath(path):
            yield f_1238(v_1237)
    return list(_hy_anon_fn_15())


# Updated at Fri Jul  3 00:31:56 2015
# By andelf
INIT_BUSLINE_STORE = pickle.load(file(
    os.path.join(os.path.dirname(__file__),
                 'data' + os.path.sep + 'bjbus_lines.pkl'), 'r'))


class BeijingBusApi(object):
    __doc__ = u'Beijing Realtime Bus API.'

    def __init__(self):
        self.opener = urllib2.build_opener()
        self.uid = u'233333333333333333333333333333333333333'
        self.opener.addheaders = [
            (u'SOURCE', u'1'), (u'PKG_SOURCE', u'1'), (u'OS', u'android'),
            (u'ROM', u'4.2.1'), (u'RESOLUTION', u'1280*720'),
            (u'MANUFACTURER', u'2013022'), (u'MODEL', u'2013022'),
            (u'UA', u'2013022,17,4.2.1,HBJ2.0,Unknown,1280*720'),
            (u'IMSI', u'233333333333333'), (u'IMEI', u'233333333333333'),
            (u'UID', self.uid), (u'CID', self.uid), (u'PRODUCT', u'nextbus'),
            (u'PLATFORM', u'android'), (u'VERSION', u'1.0.5'),
            (u'FIRST_VERSION', u'2'), (u'PRODUCTID', u'5'),
            (u'VERSIONID', u'2'), (u'CUSTOM', u'aibang')
        ]
        # FIXME: use date as update time flag is not accurate
        self.updated_time = date(2015, 7, 3)
        self.linename_cache = INIT_BUSLINE_STORE
        self.busline_info_cache = dict()

    def check_update(self):
        update_flags = self.get_update_flags()
        for flag in update_flags:
            id = flag['id']
            if flag['version'] != self.linename_cache[id]['version']:
                self.linename_cache[id] = flag
                info = self.get_busline_info(id)
                self.linename_cache[id]['linename'] = info['linename']
                print('update ... ')
        self.updated_time = date.today()

    def api_open(self, path, url_base=u'http://mc.aibang.com'):
        return self.opener.open((url_base + path)).read()

    # FIXME: this only returns first match
    def query_busline_id_by_name(self, name):
        if not isinstance(name, unicode):
            name = name.decode('utf-8')

        for flag in self.linename_cache.values():
            # A linename uses format: [Variant]<LineNo>(StartStation-EndStation)
            if flag.get('linename', u'').split(u'(')[0] == name:
                return flag['id']

        return None

    def get_update_flags(self):
        def _hy_anon_fn_19():
            f_1240 = (lambda it: {k: int(v) for (k, v) in it.items()})
            for v_1239 in xpath_etree_children_to_dict_list(
                u'//line',
                ET.fromstring(self.api_open(URL1))
            ):
                yield f_1240(v_1239)
        return list(_hy_anon_fn_19())

    def get_busline_info(self, id):
        id = int(id)
        if id in self.busline_info_cache:
            return self.busline_info_cache[id]
        # FIXME: multi-line id handling
        # xml = self.api_open(URL2.format(u'%2C'.join(map(str, ([id] + list(ids))))))
        xml = self.api_open(URL2.format(id))
        buslines = ET.fromstring(xml)
        info = list(map(decrypt_busline_etree, buslines))[0]

        # Save cache
        self.busline_info_cache[id] = info
        return info

    def get_busline_realtime_info(self, id, no):
        def _hy_anon_fn_22():
            f_1242 = (lambda it: decrypt_bus_realtime_info(it))
            for v_1241 in etree_xpath_children_to_dict_list(
                ET.fromstring(
                    self.api_open(URL3.format(id, no, 2L, 1L), URL4)),
                u'//data/bus'
            ):
                yield f_1242(v_1241)
        return list(_hy_anon_fn_22())
# end

b = BeijingBusApi()
b.check_update()


def check_update(b):
    if b.updated_time.day != date.today().day:
        b.check_update()


def _get_busline_info_by_name(busline):
    id = b.query_busline_id_by_name(unicode(busline))
    ret = b.get_busline_info(id) if id else None
    if ret:
        return ret['stations']
    return ''


def get_site_id_by_name(busline, name):
    for site in _get_busline_info_by_name(busline):
        if site['name'] == name:
            return site['no']
    return False


def get_busline_info(busline):
    check_update(b)
    stations = _get_busline_info_by_name(busline)
    if stations:
        return '\n'.join([u'第{0}站: {1}'.format(s['no'], s['name'])
                          for s in stations])
    return '查不到线路'


def get_busline_realtime_info(busline, site):
    check_update(b)
    id = b.query_busline_id_by_name(busline)
    if not site.isdigit():
        site = get_site_id_by_name(busline, site)
        if not site:
            return '请使用正确地ID或者站点名字, 查询请使用类似`公交 busline`'
    realtime_infos = b.get_busline_realtime_info(id, site)

    return '\n'.join([
        (u'*车次{0}: 下站: {1} 离下一站的距离: {2}米, 预计到达下一站的时间: {3}\n'
         u'离本站的距离: {4}米, 预计到达本站的时间: {5}').format(
             index, r['ns'], r['nsd'] if r['nsd'] != '-1' else u'进站中',
             timestamp2str(r['nst']), r['sd'],
             timestamp2str(r['st']) if r['st'] != '-1' else u'未知')
        for index, r in enumerate(realtime_infos, 1)
        if r.values().count('-1') < 3
    ])


def test_query_busline(message):
    return message.startswith(u'公交') and len(message.split()) == 2


def test_query_realtime(message):
    return u'公交' in message and len(message.split()) == 3


def test(data):
    message = data['message']
    if not isinstance(message, unicode):
        message = message.decode('utf-8')
    return test_query_busline(message) or test_query_realtime(message)


def handle(data, **kwargs):
    message = data['message']
    if not isinstance(message, unicode):
        message = message.decode('utf-8')
    # 查询公交线路
    if test_query_busline(message):
        busline = message.split()[1].strip()
        return get_busline_info(busline)
    else:
        _, busline, site_num = message.split()
        # if not busline.isdigit():
        #     return '查询公交全部站点ID和名字请使用类似`公交 busline`, 比如: 公交 571'
        return get_busline_realtime_info(busline, site_num) or '查不到线路'


if __name__ == '__main__':
    print(handle({'message': '公交 614'}))
    print(handle({'message': '公交 614 中关园'}))
    print(handle({'message': '公交 夜2'}))  # works only at night
    print(handle({'message': '公交 夜2 大红门北站'}))
