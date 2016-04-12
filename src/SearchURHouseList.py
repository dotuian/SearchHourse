#!/usr/bin/python
# -*- coding: utf-8 -*-
# filename: SearchURHouseList.py

import urllib2
import time
import datetime
import os
import codecs
import sys

import smtplib
from email import Encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from email.mime.base import MIMEBase

from bs4 import BeautifulSoup

# ==========================================
# this programe can be runed in the python2.7
# pip install urllib2
# pip install beautifulsoup4
# pip install email
# ==========================================

class FileUtils(object):
    @classmethod
    def get_all_content(self, path):
        content = ""
        for line in codecs.open(path, 'r', "utf_8") :
            content += line
        return content
        
    @classmethod
    def put_all_content(self, path, content):
        file = codecs.open(path, 'w', "utf_8")
        file.write(content)
        file.close()

class URHouseList(object):

    def __init__(self, enterpoint):
        # 团地一览的url
        self.enterpoint = enterpoint
        self.urls = self.get_all_urls()
        self.houses = self.get_all_house()
    
    def get_all_house(self): 
        houses = []
        
        #self.urls = self.urls[-3:]
        
        for url in self.urls:
            time.sleep(1)
            house = URHouse(url)
            #if house.count > 0 : 
            houses.append(house)
        return houses
            
    def get_all_urls(self):
        list = []
        
        url = "http://www.ur-net.go.jp/akiya/tokyo/20_{dcd}.html"
        
        content = urllib2.urlopen(self.enterpoint).read()
        soup = BeautifulSoup(content, "html.parser")
        for link in soup.select('tr.divisionlink td.danchi'):
            # 割引制度の個数
            for line in link.find_all('a'): 
                dcd = line["href"].split("_")[1]
                list.append(url.replace("{dcd}", dcd))
        
        return list
        
    def __str__(self):
        index = 1
        str = ""
        for house in self.houses:
            str += "No.%s%s\r\n\r\n" %(index, house)
            index = index + 1
        return str
            
    def __len__(self):
        return len(self.houses)
        

class URHouse(object):
    def __init__(self, url):
        #主页
        self.url = url
        #ajax请求url
        ajaxurl = "http://chintai.sumai.ur-net.go.jp/kanto/html_list.ashx"
        ajaxurl += "?{timestamp}&DCD={DCD}&FLOORPLAN&KUID=URK1452840344209chrome&PAGE&PRICE"
        ajaxurl += "&RANK&SCD=20&SKCD={SKCD}&SORT&SORTYPE&SYSTEM&TYPE=3&VIEW=1"
        ajaxurl = ajaxurl.replace("{DCD}", url[-9:-6])
        ajaxurl = ajaxurl.replace("{SKCD}", url[-6:-5])
        ajaxurl = ajaxurl.replace("{timestamp}", str(time.time()))
        self.ajaxurl = ajaxurl
        
        self.count = 0    #优惠件数
        self.message = ''  #优惠结果
        self.rebate = ''   #优惠制度
        
        #
        self.name = self.get_name()
        self.search()
    
    def search(self):
    
        content = urllib2.urlopen(self.ajaxurl).read()
        soup = BeautifulSoup(content, "html.parser")
    
        #割引制度有無
        for link in soup.select('dl.ft_system'):
        #for link in soup.select('dl.ft_roomplan'):
            # 优惠的个数
            self.count = len(link.find_all('dd'))
            # 优惠制度項目
            self.rebate = ', '.join(x.string for x in link.select("dd"))

        #优惠制度明细
        for link in soup.select('ul.tb_list_type table.tbList'):
            type = ""
            rent=""
            number=""
            discount=False
            # 間取り
            for value in link.select('td.rm_type'):
                type = value.string
            # 家賃
            for value in link.select('td.rm_yachin > span'):
                rent = value.string
            # 号棟
            for value in link.select('td.rm_number > a > div.sp_i > div'):
                number = value.get_text()[:-5]
            # 割引対象
            for value in link.select('td.rm_applay > p > a > img'):
                discount = True
            # 优惠种类
            for value in link.select('td.rm_applay > p > a > img'):
                info = value['alt']

            if discount :
                self.message += "%s %s %s %s\r\n" %(type, number, rent, info)

    def get_name(self):
        content = urllib2.urlopen(self.url).read()
        soup = BeautifulSoup(content, "html.parser")
        for link in soup.select('div.nm_frame h1'):
            return link.string

        return ""
        
    def should_be_sendmail(self):
        """ """
        path = "./" + datetime.datetime.now().strftime('%Y-%m-%d') + "-" + str(url[-9, -5]) + ".tmp"
        
        if not os.path.exists(path) and self.count > 0:
            return True

        if os.path.exists(path):
            str = self.get_all_content(path)
            if self.get_all_content(path) != self.message:
                return True

        return False

    def get_all_content(self, path):
        content = ""
        for line in codecs.open(path, 'r', "utf_8") :
            content += line
        return content

    def put_all_content(self, path, content):
        file = codecs.open(path, 'w', "utf_8")
        file.write(content)
        file.close()

    def __str__(self):
        result = ""
        result += "\r\n名称:" + self.name
        result += "\r\n主页:" + self.url
        if self.count > 0 :
            result += "\r\n优惠制度：" + self.rebate
            result += "\r\n================================="
            result += "\r\n" + self.message
            result += "================================="
        else:
            result += "\r\n优惠制度：暂时没有" 
        
        return result      

### ###
if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    enterpoint = "http://www.ur-net.go.jp/akiya/sonomama/tokyo.html"
    houses = URHouseList(enterpoint)
    print(houses)
    
    FileUtils.put_all_content("./result.txt", "%s" %(houses))
    
    print("finished!")
    
