# coding=utf-8
import re
import hashlib
from functools import partial

from flask import current_app as app
import requests

from baidumap import address2geo
from utils import gen_attachment

description = """
[大众点评]查找附近美食: "[城市名(默认北京市, 要带`市`)] xx有什么美食|xx附近美食 [带图] [私聊]"，比如：
* 酒仙桥附近美食
* 上海市 宜山路455号有什么美食(上海uber)
"""

API_URL = 'http://api.dianping.com/v1/{0}/{1}'
TEST_TXT_REGEX = re.compile(r'(.*)\(.*\.\.\.\)')
GOODS_REGEX = re.compile(r'(.*)附近美食|(.*)有什么美食|(.*?)美食(.*?)')
CITY_REGEX = re.compile(ur'(\W?)(.*)市', re.UNICODE)


def real_name(name):
    match = TEST_TXT_REGEX.search(name)
    if match:
        name = match.groups()[0]
    return name


def concat_params(appkey, secret, params):
    codec = appkey
    for key in sorted(params.keys()):
        codec += key + str(params[key])

    codec += secret

    # 签名计算
    sign = (hashlib.sha1(codec).hexdigest()).upper()

    url_trail = 'appkey=' + appkey + '&sign=' + sign
    for pair in params.items():
        url_trail += '&' + pair[0] + '=' + str(pair[1])
    return '?' + url_trail


class DianpingApi(object):
    def __init__(self, appkey, secret):
        self.concat_params = partial(concat_params, appkey, secret)

    def bind_api(self, path, subpath, params):
        params.pop('self')
        path_url = API_URL.format(path, subpath) + self.concat_params(params)
        r = requests.get(path_url)
        return r.json()

    def get_business_info(self, business, details=False):
        url = business['business_url']  # 商户页面URL链接
        # id = business['business_id']
        distance = business['distance']  # 商户与参数坐标的距离，单位为米
        # coupon_description = business['coupon_description']  # 优惠券描述
        # deals_description = ','.join([
        #     c['description'] for c in business['deals']])  # 团购描述
        name = real_name(business['name'])  # 商户名
        # branch_name = business['branch_name']  # 分店名
        address = business['address']  # 地址
        telephone = business['telephone']  # 电话
        # avg_rating = business['avg_rating']  # 星级评分，5.0代表五星，4.5代表四星半，依此类推
        photo_url = business['photo_url']
        if details:
            product_grade = business['product_grade']  # noqa 产品/食品口味评价，1:一般，2:尚可，3:好，4:很好，5:非常好
            # decoration_grade = business['decoration_grade']  # 环境评价 同上
            # service_grade = business['service_grade']  # 服务评价 同上
            # avg_price = business['avg_price']  # 均价格，单位:元，若没有人均，返回-1
        text = u'<{0}|{1}> {2} {3} 距离: {4} '.format(
            url, name, address, telephone, distance)
        attach = gen_attachment(
            u'{0} {1} 距离: {2}'.format(address, telephone, distance),
            photo_url, image_type='thumb', title=name, title_link=url)
        return text, attach

    def find_businesses(self, latitude, longitude, city='上海',
                        category='美食', sort=1, limit=20, offset_type=1,
                        out_offset_type=1, platform=2):
        return self.bind_api('business', 'find_businesses',
                             locals())['businesses']

    def get_single_business(self, business_id, out_offset_type=1, platform=1):
        return self.bind_api('business', 'get_single_business',
                             locals())['businesses']

    def get_all_id_list(self, city='北京'):
        return self.bind_api('reservation', 'get_all_id_list',
                             locals())['id_list']

    def get_batch_businesses_by_id(self, business_ids, out_offset_type=1):
        if isinstance(business_ids, str):
            business_ids = business_ids.split(',')
        return self.bind_api('reservation', 'get_batch_businesses_by_id',
                             locals())['businesses']

    def find_businesses_with_reservations(self, reservation_date,
                                          reservation_time, number_of_people):
        return self.bind_api('reservation',
                             'find_businesses_with_reservations',
                             locals())['businesses']


def test(data):
    return any([i in data['message']
                for i in ['有什么美食', '大众点评', '附近美食']])


def handle(data):
    message = data['message']
    if app is None:
        appkey = '41502445'
        secret = 'f0c2cc0b4f1048bebffc1527acbaeeb8'
        ak = '18691b8e4206238f331ad2e1ca88357e'
    else:
        appkey = app.config.get('DIANPING_APPKEY')
        secret = app.config.get('DIANPING_SECRET')
        ak = app.config.get('BAIDU_AK')
    api = DianpingApi(appkey, secret)

    match = CITY_REGEX.search(message.decode('utf-8'))
    city = match.groups()[1].encode('utf-8') if match else '北京'

    match = GOODS_REGEX.search(message)
    limit = 20
    if match:
        address = next((m for m in match.groups() if m is not None), '')
        geo = address2geo(ak, address)
        if not geo:
            return '找不到这个地址的数据'
        res = api.find_businesses(geo['lat'], geo['lng'], city=city)
    else:
        business_ids = api.get_all_id_list(city)
        res = api.get_batch_businesses_by_id(business_ids[:limit])
    ret = [api.get_business_info(r) for r in res]
    return '\n'.join([r[0] for r in ret]), [r[1] for r in ret]


if __name__ == '__main__':
    print handle({'message': '酒仙桥附近美食'})
    print handle({'message': '上海市 宜山路455号有什么美食(上海uber)'})
