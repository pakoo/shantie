#/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
import tornado.template
import tornado.httpserver
import logging
from BeautifulSoup import BeautifulSoup
import time
import pymongo
from datetime import datetime
import requests
import mdb


db = mdb.con.air.pm



def get_access_token(appid,appsecret):
    """
    获取app access token
    """
    token_url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s"%(appid,    appsecret)
    access_token = json.loads(requests.get(token_url).text)['access_token']
    return access_token

text_tmp = """
<xml>
    <ToUserName><![CDATA[%s]]></ToUserName>
    <FromUserName><![CDATA[%s]]></FromUserName>
    <CreateTime>%s</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[%s]]></Content>
    <FuncFlag>0</FuncFlag>
</xml> 
            """

news_tmp = """
<xml>
    <ToUserName><![CDATA[%s]]></ToUserName>
    <FromUserName><![CDATA[%s]]></FromUserName>
    <CreateTime>%s</CreateTime>
    <MsgType><![CDATA[news]]></MsgType>
    <Content><![CDATA[]]></Content>
    <ArticleCount>%s</ArticleCount>
    <Articles>
    %s
    </Articles>
</xml> 
           """

item_tmp = """
    <item>
        <Title><![CDATA[%s]]></Title>
        <Description><![CDATA[%s]]></Description>
        <PicUrl><![CDATA[%s]]></PicUrl>
        <Url><![CDATA[%s]]></Url>
    </item>
           """

air_tmp = """
<html>
<title>上海pm2.5指数为:%s</title>
<body>
<h1>图片为上海现在外滩空气状况</h1>
<p>消息来自微信公共号:美领馆pm2.5查询</p>
<img src = "http://www.semc.gov.cn/aqi/home/images/landscape.jpg" width="100%%" >
<h2>可按右上角按钮分享到朋友圈</h2>
</body>
</html>
"""

img_tmp="""
<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>
<MsgType><![CDATA[image]]></MsgType>
<Image>
<MediaId><![CDATA[%s]]></MediaId>
</Image>
</xml>
"""

def get_pm(place):
    res = db.find_one({'location':place},sort=[('create_time',-1)])    
    if res:
        return res

def get_level(data):
    if 0<= data <=50:
        return "空气状况:优"
    elif 51<= data <=100: 
        return "空气状况:良"
    elif 101<= data <=150: 
        return "空气状况:轻度污染,建议佩戴口罩"
    elif 151<= data <=200: 
        return "空气状况:中度污染,建议佩戴口罩"
    elif 201<= data <=300: 
        return "空气状况:重度污染,建议不外出"
    else:
        return "空气状况:严重污染,建议不外出"

def update_menu():
    """
    更新菜单
    """
    menu = {
        "button":[
                    { 
                    #"type":"click",
                    "name":"城市",
                    "sub_button":[
                                {
                                "type":"click",
                                "name":"上海",
                                "key":"shanghai"
                                },
                                {
                                "type":"click",
                                "name":"北京",
                                "key":"beijing"
                                },
                                {
                                "type":"click",
                                "name":"广州",
                                "key":"guangzhou"
                                },
                                {
                                "type":"click",
                                "name":"成都",
                                "key":"chengdu"
                                },
                                ]
                    },

                    {
                    "type":"view",
                    "name":"官网",
                    "url":"http://www.oucena.com/"
                    },

                ]
    }


class weixin(tornado.web.RequestHandler):

    def prepare(self):
        print '\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
        print 'request:',self.request
        print 'body:',self.request.body
        print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
        if self.request.method == 'POST':
            soup = BeautifulSoup(self.request.body)
            self.userid  = soup.find('fromusername').text
            self.createtime = soup.find('createtime').text
            self.msgtype = soup.find('msgtype').text
            self.myid = soup.find('tousername').text
            if self.msgtype == 'text':
                self.wxtext = soup.find('content').text
                print 'text:',self.wxtext  
            elif self.msgtype == 'location':
                self.location_x = soup.find('location_x').text 
                self.location_y = soup.find('location_y').text 
                self.location_scale = soup.find('scale').text 
                self.location_lable = soup.find('label').text 
                print 'x:',self.location_x  
                print 'y:',self.location_y
            elif self.msgtype == 'image':
                self.picurl = soup.find('picurl').text 
                print 'pic url:',self.picurl 
            elif self.msgtype == 'event':
                self.event = soup.find('event').text
                self.event_key = soup.find('eventkey').text
        else:
            logging.info('request:%s'%self.request) 

    def get(self):
        logging.info('arguments:%s'%str(self.get_arguments('echostr','')))
        print 'echostr:',self.get_arguments('echostr','')
        self.finish(self.get_argument('echostr',''))
        #items = [('title1','description1','http://oucena.com/static/img/bt.jpg','http://oucena.com/')]  
        #items_str = '\n'.join([item_tmp%i for i in items])
        #logging.info(items_str)
        #res = news_tmp%('asd','sdf',1287324,len(items),items_str) 
        #self.finish(res)

    def post(self):
        if self.msgtype == 'text':
            if self.wxtext in ('1','shanghai','上海') :
                res = get_pm('shanghai')
                pm25 = res['data']
                ctime = str(res['publish_time'])
                place = '上海'
            elif self.wxtext in ('2','北京','beijing'):
                res = get_pm('beijing')
                pm25 = res['data']
                ctime = str(res['publish_time'])
                place = '北京'
            elif self.wxtext in ('3','广州','guangzhou'):
                res = get_pm('guangzhou')
                pm25 = res['data']
                ctime = str(res['publish_time'])
                place = '广州'
            elif self.wxtext in ('4','成都','chengdu'):
                res = get_pm('chengdu')
                pm25 = res['data']
                ctime = str(res['publish_time'])
                place = '成都'
            elif self.wxtext == '5':
                items = [('title1','description1','http://oucena.com/static/img/bt.jpg','http://oucena.com/airpic?pm25=18')]  
                self.send_news(items)
            else:
                a = """发送 “1”查询上海 美国领事馆发布的 pm2.5 数据
                     \n发送 “2”查询北京 美国领事馆发布的 pm2.5 数据
                     \n发送 “3”查询广州 美国领事馆发布的 pm2.5 数据
                     \n发送 “4”查询成都 美国领事馆发布的 pm2.5 数据
                    """
                self.send_text(a)    
                return 
            air_level =get_level(int(float(pm25)))  
            msg = "%s %s PM2.5:%s  %s "%(ctime,place,pm25,air_level)
            if self.wxtext =="1":
                self.send_air_pic(pm25,msg)
            else:
                self.send_text(msg)    
        elif self.msgtype == 'location':
            self.send_text('我收到你消息啦!!')
        elif self.msgtype == 'image':
            self.send_text('我收到你消息啦!!')
        elif self.msgtype == 'event':
            print 'eventkey:',self.event_key
            if self.event_key == 'about':
                items = [(u'天津瀚福精密液压技术有限公司简介',u'天津瀚福精密液压技术有限公司坐落于渤海明珠天津海河科技园，聚集了多位热爱液压行业，专注于液压技术创新，以发展提升民族液压水平为使命的行业资深人士共同创立，自创品牌 HANFOOK 瀚福液压。','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPMibjnepxoNYic8nZNZIibJVpYQa7UF8oe8OguJB4iaXfCwQXN2feSIdL09DxOG8diaIeYQhYrR0EJicag/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013066&itemidx=1&sign=c5ea293cf7b1a58e6ccae9546e85a0c8#wechat_redirect')]  
                self.send_news(items)
                #self.send_text(u"""天津瀚福精密液压技术有限公司坐落于渤海明珠天津海河科技园，聚集了多位热爱液压行业，专注于液压技术创新，以发展提升民族液压水平为使命的行业资深人士共同创立，自创品牌 HANFOOK 瀚福液压。 瀚，寓意液压广泛的应用领域和瀚福人追求更宽广、博大的幸福的胸怀；  福，寓意来自中国的民族液压品牌，和体现瀚福人为公司及社会创造价值和福祉的企业文化。瀚福液压旨在为客户产品增值、节能，与供应链共同降本、增效，通过技术创新、无限服务、应需而变、紧密合作实现多赢共赢。致力于液压系统的高度集成与方案优化，为液压领域提供全方位的解决方案是我们的企业目标与追求；共福共赢，成就你我，成为液压技术世界领先品牌是瀚福液压的企业梦想和愿景。""")
            if self.event_key == 'findme':
                self.send_text(u"""地 址：天津市津南区海河科技园聚兴道6号
邮 编：300350
电 话：+86-22 - 2576 3306
传 真：+86-22 - 2576 0933
E-mail：hanfook@hanfook.com.cn
网 址：www.hanfook.com.cn
                        """)
            elif self.event_key == 'products':
                items = [
                        (u'产品中心',u'产品中心',u'http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPMibjnepxoNYic8nZNZIibJVpYQa7UF8oe8OguJB4iaXfCwQXN2feSIdL09DxOG8diaIeYQhYrR0EJicag/0','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEA26Ap7ZrVoXkiaJPXHsFqhVtdNDZ1yO0t16SQF2TNMEWhcoVu9BzzBxA/0'),
    (u'二通插装阀',u'二通插装阀','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEALnAp6HsRo3ias1eOKOW9CVwJ5rA7S9BOSCpulQFjmViaiacXJa9eg0SOA/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013044&itemidx=1&sign=99723752c60ccecbae35df500d214b0b'),
    (u'方向控制阀',u'方向控制阀','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEAsfK9JXMspoib3WQX1I7OMbWTqLC28X2ac7p8yPo6GcU5VBsu6UyQMog/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013047&itemidx=1&sign=2066b954dac85a363e9a761d540966b5#wechat_redirect'),
    (u'叠加阀',u'叠加阀','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEAAFRicS1NfXQUIUQ3WXAicuDSaVS3TEl4KYVqBrtAZtfgWRx9zatd85Og/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013049&itemidx=1&sign=5f7130560546d79a760208ad36ab1925#wechat_redirect'),
    (u'压力/流量控制阀',u'压力/流量控制阀','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEAwHFZ2GfZT769nO1Og9Gj9xlxyGH0sia3zThp0C6pic3Dekk0MACiayqIg/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013051&itemidx=1&sign=a5c5f8dfb7747fa5e42255fcc385ac05#wechat_redirect'),
    (u'比例阀',u'比例阀','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEAmsI4NRYCMTOLvEW7f2YYnsY78SZRh4jDj5cK0lmRs4iaVzatbkBgqLg/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013053&itemidx=1&sign=a8584b742c1acd95d8387f2d30bb7d8d#wechat_redirect'),
    (u'螺纹插装阀',u'螺纹插装阀','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEAwhI225ichOOpqyP2A6fZu2EXE3mB9RksicxznqoDTDXxhibvqxbSic9jpg/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013055&itemidx=1&sign=f58dbde32bbd37a6e3722e63e25ea9e4#wechat_redirect'),
    (u'冷却系列',u'冷却系列','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEA0NoiapGIa74Zx4InquUr1g9a0wntB0HBrY4AHbDQt8fjY7WNV0LeX1A/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013057&itemidx=1&sign=3b5f3e0a1c08de43cb1ad9e9a5e5ed2f#wechat_redirect'),
    (u'液压泵',u'液压泵','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEAmGSDdWQBRD41hZJNY159PcoyDoql49ib08rrQWZQ6KykqtaGFx1oZpQ/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013059&itemidx=1&sign=4250630526ba06a62f9329e603355f9e#wechat_redirect'),
    #(u'动力单元',u'动力单元','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEACqx0yfY93cdVgcn7PFYVKyhkdHC2V5Fic8HZPRf7nrGnciaIIMwkxoXw/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013061&itemidx=1&sign=8214adde9fa926debb985100c9225e1e#wechat_redirect'),
    (u'液压系统',u'液压系统','http://mmbiz.qpic.cn/mmbiz/Qhd1mSib1dTPGtZwGfJwSHY50MFDpzMEAQzzeJpA6PPicxzqy5KYttAmbnlic2WPOLogiaoedqAKaGia6deJqialoVXA/0','http://mp.weixin.qq.com/mp/appmsg/show?__biz=MjM5NDAxOTk5OQ==&appmsgid=10013063&itemidx=1&sign=a393a063862a354a593ada1332535229#wechat_redirect'),
                        ]  

                self.send_news(items)

    def send_text(self,msg):
        #self.set_header("Content-Type","application/xml; charset=UTF-8")
        line = text_tmp%(self.userid,self.myid,int(time.time()),msg) 
        self.finish(line)

    def send_news(self,items):
        """
        发送图文
        """
        items_str = '\n'.join([item_tmp%i for i in items])
        logging.info(items_str)
        res = news_tmp%(self.userid,self.myid,int(time.time()),len(items),items_str) 
        self.finish(res)

    def send_air_pic(self,pm25,msg):
        pic_url = self.get_shanghai_air_pic()
        items = [('上海PM2.5浓度为:%s'%pm25,msg,pic_url,"http://oucena.com/airpic?pm25=%s"%pm25)]  
        #items = [('上海PM2.5浓度为:%s'%pm25,msg,pic_url,pic_url)]  
        self.send_news(items)

    def send_pic(self,imgid):
        """
        发送图片
        """
        res = img_tmp%(self.userid,self.myid,int(time.time()),imgid)
        self.finish()


    def get_shanghai_air_pic(self):
        n = datetime.now()
        if n.month < 10:
            month = "0%s"%n.month
        else:
            month = n.month
        if n.day < 10:
            day = "0%s"%n.day
        else:
            day = n.day
        if n.hour < 10:
            hour = "0%s"%(n.hour-1)
        else:
            hour = n.hour-1
        url = "http://www.semc.gov.cn/aqi/home/images/pic/%s%s%s%s00.jpg"%(n.year,month,day,hour)
        #print 'shanghai air pic:',url
        #return url
        return "http://www.semc.gov.cn/aqi/home/images/landscape.jpg"
        
        
class AirPic(tornado.web.RequestHandler):

    def get(self):
	pm25 = self.get_argument("pm25")
	print 'pm25:',pm25
        self.finish(air_tmp%pm25)
            
class towww(tornado.web.RequestHandler):

    def get(self):
        uri = self.uri     
        print 'uri:',self.uri
        self.finish(self.uri)
        #self.redirect('www.404cn.org'+slef.uri, permanent=True)

class tufuli(tornado.web.RequestHandler):

    def get(self):
        self.finish('b97ac2b5f862000c013621616f783a78')
        #self.redirect('www.404cn.org'+slef.uri, permanent=True)
        
class www(tornado.web.RequestHandler):

    def get(self):
        #loader = tornado.template.Loader("./tufuli/")
        #self.finish(loader.load('base.html').generate({}))
        self.render('tufuli/base.html',mainpage='active')


class Application(tornado.web.Application):
    def __init__(self):
        app_settings={
            'debug':True,
        }
        handlers = [
            (r'/',weixin),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {"path": "./static"}),
        ]
        tornado.web.Application.__init__(self,handlers,**app_settings)

if __name__ == '__main__':
    pass
    http_server = tornado.httpserver.HTTPServer(request_callback=Application())
    http_server.listen(80)
    tornado.ioloop.IOLoop.instance().start()

    #print get_all_item()[0]
    #add_new_keyword('macbook air')
    #print get_all_keyword()
