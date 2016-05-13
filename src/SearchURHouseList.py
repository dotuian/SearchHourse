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
from email.header import Header

from bs4 import BeautifulSoup

# ==========================================
# this programe can be runed in the python2.7
# pip install urllib2
# pip install beautifulsoup4
# pip install email
# ==========================================


class FileUtils(object):
    ''' 文件读写工具类 '''
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
        
class SendMailer(object):
    ''' 邮件发送类 '''
    
    def __init__(self, to, subject, body):
        #送信服务器配置 
        self.SMTP = "mail.xxxxxx.jp"
        self.PORT = "587"
        self.USERNAME ="xxxxxx@xxxxxx.jp"
        self.PASSWARD = 'xxxxxx'
        
        self.to = to
        self.subject = subject
        self.body =body
        
    def sendmail(self):
        ''' 发送邮件 '''
        message = MIMEMultipart("alternative")
        message.set_charset("utf-8")
        
        message["From"] = self.USERNAME
        message["To"] = self.USERNAME
        message["Date"] = formatdate()
        message["Subject"] = Header(self.subject.encode('utf-8'), 'UTF-8').encode()

        body = MIMEText(self.body.encode('utf-8'), 'plain','utf-8')
        #body = MIMEText(body, 'plain','utf-8')
        message.attach(body)

        #发信操作        
        smtpobj = smtplib.SMTP(self.SMTP, self.PORT)
        smtpobj.ehlo()
        smtpobj.starttls()
        smtpobj.ehlo()
        smtpobj.login(self.USERNAME, self.PASSWARD)
        smtpobj.sendmail(self.USERNAME, self.to, message.as_string())
        smtpobj.close()


class URHouseManager(object):
    ''' 团地信息管理类  '''
    def __init__(self, *args, **kwargs):
        #初始化准备
        self.houses = []
        self.urls = []
        self.discount = 0 #优惠团地个数
        self.path = "./result.txt" #检索结果保存 
        
        #根据参数的不同，来执行不同的操作
        enterpoint = kwargs.get('enterpoint') 
        if enterpoint:
            #自动抓取所有团地信息
            self.urls = self.get_all_urls(enterpoint)
            #获取所有团地的信息
            self.houses = self.get_all_house()            
        else:
            #获取指定团地的信息
            self.urls = kwargs.get('urls')
            #获取指定团地的信息
            self.houses = self.get_all_house()


    def get_all_house(self): 
        houses = []
        
        #self.urls = self.urls[-3:]
        
        for url in self.urls: 
            time.sleep(1)
            house = URHouse(url)
            #一个团地优惠房子的个数>0是，优惠团地数自增
            if house.count > 0:
                #优惠团地的个数
                 self.discount = self.discount + 1
            houses.append(house)
        return houses
            
    def get_all_urls(self, enterpoint):
        list = []
        
        url = "http://www.ur-net.go.jp/akiya/tokyo/20_{dcd}.html"
        
        content = urllib2.urlopen(enterpoint).read()
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
    
    
    def notify(self, mailler):
        """ """
        flag = False
        if not os.path.exists(self.path) and self.discount > 0:
            flag = True

        if os.path.exists(self.path):
            oldResult = self.get_result()
            newResult = "%s" %(self)
            if oldResult != newResult:
                flag = True
        
        if flag :
            print("发送邮件\n")
            mailler.sendmail()
        
            #结果保存
            self.save_result()
        
        return flag
    
    def save_result(self):
        FileUtils.put_all_content(self.path, str(self))
        
    def get_result(self):
        #获取保存结果
        return FileUtils.get_all_content(self.path)

        
class URHouse(object):
    ''' 团地对象 '''
    
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
    
    
    if False:
        #获取所有团地的信息
        enterpoint = "http://www.ur-net.go.jp/akiya/sonomama/tokyo.html"
        houses = URHouseManager(enterpoint = enterpoint)
    else:
        #获取指定团地的信息
        urls = [
                "http://www.ur-net.go.jp/akiya/tokyo/20_3070.html",
                "http://www.ur-net.go.jp/akiya/tokyo/20_1650.html",
                "http://www.ur-net.go.jp/akiya/tokyo/20_6400.html",
                "http://www.ur-net.go.jp/akiya/tokyo/20_2810.html",
                #"http://www.ur-net.go.jp/akiya/tokyo/20_6771.html",
            ]
        houses = URHouseManager(urls = urls)

    print(houses)
    
    #通知结果
    houses.notify(SendMailer(
                 ["xxxxxx@xxxxxx.com", "xxxxxx@qq.com", "63734524@qq.com"],    
                 "【通知】UR団地情報異動", 
                 str(houses)
             ))
    
    print("finished!")
    
