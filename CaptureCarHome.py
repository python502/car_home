#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/22 20:37
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    :
# @File    : CaptureCarHome.py
# @Software: PyCharm
# @Desc    :
import gevent
from CaptureBase import CaptureBase

import re
import copy
import time

from logger import logger
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urlparse import urljoin

class CaptureCarHome(CaptureBase):
    home_url = 'https://car.autohome.com.cn/'
    left_list_new = 'https://car.autohome.com.cn/AsLeftMenu/As_LeftListNew.ashx?typeId=1%20&brandId=0%20&fctId=0%20&seriesId=0'
    city_id = '310100'
    HEADER = '''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7
            Host: car.autohome.com.cn
            User-Agent: {}
            '''
    Config_Title = {u'\u57fa\u672c\u53c2\u6570': '00',
                    u'\u8f66\u8eab': '01',
                    u'\u53d1\u52a8\u673a': '02',
                    u'\u7535\u52a8\u673a': '03',
                    u'\u53d8\u901f\u7bb1': '04',
                    u'\u5e95\u76d8\u8f6c\u5411': '05',
                    u'\u8f66\u8f6e\u5236\u52a8': '06',
                    u'\u4e3b\u002f\u88ab\u52a8\u5b89\u5168\u88c5\u5907': '07',
                    u'\u8f85\u52a9\u002f\u64cd\u63a7\u914d\u7f6e': '08',
                    u'\u5916\u90e8\u002f\u9632\u76d7\u914d\u7f6e': '09',
                    u'\u5185\u90e8\u914d\u7f6e': '10',
                    u'\u5ea7\u6905\u914d\u7f6e': '11',
                    u'\u591a\u5a92\u4f53\u914d\u7f6e': '12',
                    u'\u706f\u5149\u914d\u7f6e': '13',
                    u'\u73bb\u7483\u002f\u540e\u89c6\u955c': '14',
                    u'\u7a7a\u8c03\u002f\u51b0\u7bb1': '15',
                    }
    def __init__(self, user_agent, proxy_ip=None):
        super(CaptureCarHome, self).__init__(user_agent, proxy_ip)
        self.header = self._getDict4str(self.HEADER.format(self.user_agent))
        self.error_series_url = []
        self.error_spceconfig_url = []

    def __del__(self):
        super(CaptureCarHome, self).__del__()

    def _get_logo_url(self, brands_url):
        page_source = self.getHtml(brands_url, self.header)
        try:
            pattern = re.compile('img src="//car[\d]*\.autoimg\.cn/cardfs/brand/100[\s\S]*?">', re.S)
            logo_url = pattern.findall(page_source)[0]
        except IndexError:
            pattern = re.compile('img src="//car[\d]*\.autoimg\.cn/logo/brand/100[\s\S]*?">', re.S)
            logo_url = pattern.findall(page_source)[0]
        logo_url = logo_url[9:-2]
        # soup = BeautifulSoup(page_source, 'html.parser')
        # logo_url = soup.find('div', {'class':'uibox-con contbox'}).find('div', {'class':'carbradn-pic'}).find('img').attrs['src']
        return urljoin(self.home_url, logo_url)

    def getCarBrands(self, logo = False):
        results = []
        page_source = self.getHtml(self.left_list_new, self.header)
        page_source = page_source[18:-3]
        soup = BeautifulSoup(page_source, 'lxml')
        cartree_letter = soup.findAll('div', {'class': "cartree-letter"})
        uls = soup.findAll('ul')
        for (letter, ul) in zip(cartree_letter, uls):
            letter = letter.getText()
            lis = ul.findAll('li')
            for li in lis:
                result = {}
                result['brands_id'] = li.attrs['id'][1:]
                patter = re.compile('\(\d+\)')
                s = patter.search(li.getText()).group(0)
                n = len(s)
                result['brands_name'] = li.getText()[:-n]
                result['initials'] = letter
                url = li.find('a').attrs['href']
                result['brands_url'] = urljoin(self.home_url, url)
                if logo:
                    result['logo_url'] = self._get_logo_url(result['brands_url'])
                results.append(result)
        return results

    def saveCarBrands(self, car_brands):
        good_datas = car_brands
        table = 'car_home_brands'
        replace_columns = ['brands_id', 'brands_name', 'brands_url', 'initials', 'logo_url']
        return self._save_datas(good_datas, table, replace_columns)

    def dealCarBrands(self):
        car_brands = self.getCarBrands(logo=True)
        return self.saveCarBrands(car_brands)

    def getCarSeries(self, brands_url, brands_id):
        try:
            results = []
            page_source = self.getHtml(brands_url, self.header)
            page_source = page_source.decode("gb2312", errors='ignore')
            soup = BeautifulSoup(page_source, 'html.parser')
            carbradn_conts = soup.find('div', {'class': 'carbradn-cont fn-clear'}).findAll('dl', {'class': 'list-dl'})
            for carbradn_cont in carbradn_conts:
                result = {}
                result['brands_id'] = brands_id
                result['series_local'] = carbradn_cont.find('dt').getText()
                car_types = carbradn_cont.find('dd').findAll('div', {'class': 'list-dl-name'})
                car_names = carbradn_cont.find('dd').findAll('div', {'class': 'list-dl-text'})
                for (types, names) in zip(car_types, car_names):
                    infos = names.findAll('a')
                    for info in infos:
                        copy_result = copy.copy(result)
                        copy_result['series_type'] = types.getText()[:-1]
                        href = info.attrs['href']
                        copy_result['series_url'] = urljoin(self.home_url, href)
                        copy_result['series_id'] = int(href.split('-')[1].split('.')[0])
                        copy_result['series_name'] = info.attrs['title']
                        copy_result['is_stock'] = 1 if info.attrs['title'].find(u'\u505c\u552e') == -1 else 0
                        results.append(copy_result)
            return results
        except Exception, e:
            self.error_series_url.append(brands_url)
            logger.error('getCarSeries error:{},brands_url:{}'.format(e, brands_url))
            return []

    def saveCarSeries(self, car_series):
        good_datas = car_series
        table = 'car_home_series'
        replace_columns = ['series_id', 'brands_id', 'series_name', 'series_local', 'series_type', 'series_url', 'is_stock']
        return self._save_datas(good_datas, table, replace_columns)

    def get_all_series(self):
        car_series_datas = []
        car_brands = self.getCarBrands()
        # car_brands = car_brands[:10]
        # funlist = [gevent.spawn(self.getCarSeries, car_brand.get('brands_url'), car_brand.get('brands_id')) for car_brand in car_brands if car_brand.get('brands_id') == '33']
        funlist = [gevent.spawn(self.getCarSeries, car_brand.get('brands_url'), car_brand.get('brands_id')) for car_brand in car_brands]
        jobs = gevent.joinall(funlist)
        [car_series_datas.extend(job.value) for job in jobs]
        return car_series_datas
    def dealCarSeries(self):
        car_series_datas = self.get_all_series()
        return self.saveCarSeries(car_series_datas)

    def get_derler_prices(self, derler_price_url, header):
        page_source = self.getHtml(derler_price_url, header)
        page_source = page_source[16:-1].decode("gb2312", errors='ignore').encode('utf-8')
        derler_infos = json.loads(page_source).get('body').get('item')
        return derler_infos

    def getCarInfos(self, car_models_data, header):
        url = 'https://dealer.autohome.com.cn/Price/_SpecConfig?DealerId={}&SpecId={}&seriesId={}'.format(car_models_data.get('dealer_id'), car_models_data.get('model_id'), car_models_data.get('series_id'))
        page_source = self.getHtml(url, header)
        page_source = page_source.decode("gb2312", errors='ignore').encode('utf-8')
        soup = BeautifulSoup(page_source, 'html.parser')
        config_tables = soup.findAll('table', {'class': 'config-table'})
        config_titles = soup.findAll('div', {'class': 'config-title'})
        if len(config_tables) is not len(config_titles) or not len(config_tables) or not len(config_titles):
            self.error_spceconfig_url.append(url)
            raise ValueError('url:{} len config_tables not equal len config_title'.format(url))
        # for n in range(1):
        for n in range(len(config_tables)):
            title = config_titles[n].getText()
            tds = config_tables[n].findAll('td')
            for m in range(len(tds)):
                x = str(self.Config_Title.get(title)).zfill(2)
                y = str(m).zfill(2)
                t = 't{}p{}'.format(x, y)
                car_models_data[t] = tds[m].getText()

    def getSpecList(self, spec_url, header):
        page_source = self.getHtml(spec_url, header)
        page_source = page_source.decode("gb2312", errors='ignore').encode('utf-8')
        derler_infos = json.loads(page_source).get('result').get('list')
        return derler_infos

    def getCarModels(self, series_data):
        car_models_datas = []
        derler_price_url = 'https://carif.api.autohome.com.cn/dealer/LoadDealerPrice.ashx?_callback=LoadDealerPrice&type=1&seriesid={}&city={}'.format(series_data.get('series_id'), self.city_id)
        header = {'Referer': series_data.get('series_url'), 'User-Agent': self.user_agent}
        first_flag = True
        derler_prices = self.get_derler_prices(derler_price_url, header)
        spec_infos = []
        for derler_price in derler_prices:
            car_models_data = {}
            car_models_data['brands_id'] = series_data.get('brands_id')
            car_models_data['series_id'] = series_data.get('series_id')
            car_models_data['model_id'] = derler_price.get('SpecId')
            car_models_data['dealer_id'] = derler_price.get('DealerId')
            car_models_data['city_id'] = self.city_id
            header_spec = {'Accept': 'application/json, text/javascript, */*; q=0.01', 'Referer': derler_price.get('Url'), 'User-Agent': self.user_agent}
            if first_flag:
                spec_url = 'https://dealer.autohome.com.cn/Ajax/GetSpecListByDealer?dealerId={}&seriesId={}'.format(
                    derler_price.get('DealerId'), series_data.get('series_id'))
                spec_infos = self.getSpecList(spec_url, header_spec)
                first_flag = False
            [spec_info for spec_info in spec_infos if spec_info['SpecId'] == derler_price.get('SpecId')]
            car_models_data['model_name'] = spec_info.get('SpecName')
            car_models_data['original_price'] = spec_info.get('OriginalPrice')
            car_models_data['price'] = spec_info.get('Price')
            try:
                self.getCarInfos(car_models_data, header_spec)
                car_models_datas.append(car_models_data)
            except ValueError, e:
                logger.error('{}'.format(e))
        return car_models_datas

    def dealCarModels(self):
        numSet = 100
        car_models_datas = []
        car_series_datas = self.get_all_series()
        num = 0
        while car_series_datas:
            new_datas = car_series_datas[:numSet]
            car_series_datas = car_series_datas[numSet:]
            funlist = [gevent.spawn(self.getCarModels, new_datas) for new_datas in new_datas if new_datas.get('is_stock') == 1]
            jobs = gevent.joinall(funlist)
            [car_models_datas.extend(job.value) for job in jobs]
            self.saveCarModels(car_models_datas)
            num+=1
            logger.info('num: {} have insert'.format(num*numSet))

    def saveCarModels(self, car_models):
        good_datas = car_models
        table = 'car_home_models'
        replace_columns = [key for key in car_models[0].iterkeys()]
        return self._save_datas(good_datas, table, replace_columns)
def main():
    startTime = datetime.now()
    useragent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'

    objCaptureAmazon = CaptureCarHome(useragent)
    # objCaptureAmazon.dealCarBrands()
    # objCaptureAmazon.dealCarSeries()
    objCaptureAmazon.dealCarModels()
    # objCaptureAmazon.get_derler_prices('https://carif.api.autohome.com.cn/dealer/LoadDealerPrice.ashx?_callback=LoadDealerPrice&type=1&seriesid=3064&city=310100',{'Referer': 'https://car.autohome.com.cn/price/series-3064.html', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'})
    # objCaptureAmazon.getSpecList(
    #     'https://dealer.autohome.com.cn/Ajax/GetSpecListByDealer?dealerId=128928&seriesId=3064',
    #     {'Accept': 'application/json, text/javascript, */*; q=0.01',
    #      'Referer': 'https://dealer.autohome.com.cn/128928/spec_31364.html',
    #      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'})
    # objCaptureAmazon.getCarInfos(
    #     # {'dealer_id':'128928','model_id':'31364','series_id':'3064'},
    #     {'dealer_id':'130337','model_id':'32790','series_id':'834'},
    #     {'Accept': 'application/json, text/javascript, */*; q=0.01', 'Referer': 'https://dealer.autohome.com.cn/128928/spec_31364.html',
    #      'Referer': 'https://dealer.autohome.com.cn/128928/spec_31364.html',
    #      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'})
    endTime = datetime.now()
    print 'seconds', (endTime - startTime).seconds
if __name__ == '__main__':
    main()

