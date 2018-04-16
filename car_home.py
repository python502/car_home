#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/13 14:15
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    : 
# @File    : test2.py
# @Software: PyCharm
# @Desc    :
#coding=utf-8
import re
import PyV8
import logging
import requests

def clscontent(alljs):
    try:
        ctx = PyV8.JSContext()
        ctx.enter()
        ctx.eval(alljs)
        return ctx.eval('rules')
    except:
        logging.exception('clscontent function exception')
        return None

def makejs(html):
    try:
        alljs = ("var rules = '';"
                 "var document = {};"
                 "document.createElement = function() {"
                 "      return {"
                 "              sheet: {"
                 "                      insertRule: function(rule, i) {"
                 "                              if (rules.length == 0) {"
                 "                                      rules = rule;"
                 "                              } else {"
                 "                                      rules = rules + '#' + rule;"
                 "                              }"
                 "                      }"
                 "              }"
                 "      }"
                 "};"
                 "document.querySelectorAll = function() {"
                 "      return {};"
                 "};"
                 "document.head = {};"
                 "document.head.appendChild = function() {};"

                 "var window = {};"
                 "window.decodeURIComponent = decodeURIComponent;")

        js = re.findall('(\(function\([a-zA-Z]{2}.*?_\).*?\(document\);)', html)
        for item in js:
            alljs = alljs + item
        alljs = alljs.encode('utf-8')
        return alljs
    except:
        logging.exception('makejs function exception')
        return None

def main(index):
    try:
        req = requests.get('https://car.autohome.com.cn/config/spec/%d.html' % index)
        # req = requests.get('https://car.autohome.com.cn/config/series/%d.html' % index)
        alljs = makejs(req.text)
        if(alljs == None):
            print('makejs error')
            return

        result = clscontent(alljs)
        if(result == None):
            print('clscontent error')
            return

        for item in result.split('#'):
            print(item)
    except:
        logging('main function exception')

if __name__ == '__main__':
    main(20248)
    #https://www.cnblogs.com/qiyueliuguang/p/8144248.html