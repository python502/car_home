import base64
# from urllib import request
# import urllib.parse
import json
import os
import random
import time
import chardet
import requests
from Log import log
from lxml import html
import BaseInfo
from ParseData import parse_data
import proxy
from JsonData import save_json
from BaseInfo import i,a
import re


"""
以图传图  python3代码   其中python2 与 python3 base64不同
"""


def fetch_image(temp,product_id,category_id,s):
    global i, a
    app_name = "pc_tusou"
    current_time = "".join(str(time.time()).split("."))[:13]
    another_current_time = "".join(str(time.time()).split("."))[:13]
    print("————————————————————————————————————————————————————————")
    print("代理服务器 | " + proxy.keep_proxy())
    file_path = BaseInfo.download_path + category_id + os.sep + product_id
    try:
        r = s.get(
            # 第一次请求
            "https://open-s.1688.com/openservice/ossDataService",
            params={
                "appName": app_name,
                "appKey": base64.b64encode("{};{}".format(app_name, current_time).encode("utf-8")),
                "callback": "",
                "_": another_current_time,
            },
            headers=BaseInfo.aliyun_headers,
        )
        # 第一次请求

        r.close()
        data = r.json().get("data")
        another_2_current_time = "".join(str(time.time()).split("."))[:10] + "000"
        t = "".join([random.choice("ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678") for i in range(10)])
        key = "cbuimgsearch/{}.jpg".format(t + another_2_current_time)
        files = {'file': ('1.jpg', temp, 'image/jpeg')}


        # 给第二次构造加密信息

        r = s.post(
            "https://cbusearch.oss-cn-shanghai.aliyuncs.com",
            data={
                "name": '1.jpg',
                "key": key,
                "policy": data.get("policy"),
                "OSSAccessKeyId": data.get("accessid"),
                "success_action_status": "200",
                "callback": "",
                "signature": data.get("signature")
                },
            files=files,
            headers=BaseInfo.aliyun_headers,
            )
        # 第二次请求

        r.close()
        code_status = r.status_code
        # 查看状态吗

        r = s.get(
            "https://s.1688.com/youyuan/index.htm?tab=imageSearch&imageType=oss&imageAddress={}".format(key),
            headers=BaseInfo.aliyun_headers,
        )
        # 第三次次请求

        r.close()
        charset = chardet.detect(r.content)
        tree = html.fromstring(r.content.decode(charset.get("encoding")))
        register = tree.xpath('//*[@id="masthead-v4"]/div/h1/span/text()')
        code = tree.xpath('//div[@class="sm-offer sm-offer-fc"]/script/text()')[0]

        code = code.replace('_pagedata_["offerlist"] = ', "")
        test = json.loads(code)

        if test.get("offerList") != [] and register != '登录':
            parse_data(code, product_id, code_status, temp,s)
            i += 1
            log("log", file_path)
            print("匹配到的商品个数————————>>{}\n".format(i))
        elif register == '登录':
            print("error!!!! 1688 page has changed, pop next proxy")
            if proxy.proxy_next():
                proxy.proxy_next()
            else:
                proxy.get_proxy()
                proxy.proxy_next()
                log("error", file_path)


    except Exception as f:
        print(f)
        print("error!!!! 1688 page has changed, pop next proxy")
        if re.findall("Max retries exceeded with url",str(f)):
            time.sleep(2)
            if proxy.proxy_next():
                time.sleep(2)
                proxy.proxy_next()
            else:
                proxy.get_proxy()
                proxy.proxy_next()
                log("error", file_path)
            print("代理服务器 | " + proxy.keep_proxy())
        else:
            if proxy.proxy_next():
                time.sleep(0.5)
                proxy.proxy_next()
            else:
                proxy.get_proxy()
                proxy.proxy_next()
                log("error", file_path)
            print("代理服务器 | " + proxy.keep_proxy())
