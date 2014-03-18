#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
some db interface 
"""
from config import *
from django.utils.encoding import smart_str, smart_unicode
import datetime
import types
import os.path
from urlparse import urlparse
import urllib
import BeautifulSoup as bsoup
from bs4 import BeautifulSoup as bs4,Tag

mktime=lambda dt:time.mktime(dt.utctimetuple())
######################db.init######################

post=kds.post
kdsuser=kds.user

tieba_post = baidu.post

browser = requests.session()
######################gfw.init######################
gfw = GFW()
gfw.set(open(os.path.join(os.path.dirname(__file__),'keyword.txt')).read().split('\n'))

lgfw = GFW()
lgfw.set(['thunder://','magnet:','ed2k://'])


tongji = """
<center>
<script language="javascript" type="text/javascript" src="http://js.users.51.la/5988086.js"></script>
<noscript><a href="http://www.51.la/?5988086" target="_blank">
<img alt="&#x6211;&#x8981;&#x5566;&#x514D;&#x8D39;&#x7EDF;&#x8BA1;" src="http://img.users.51.la/5988086.asp" style="border:none" /></a>
</noscript>
</center>
"""

def post_insert(para,dbname=None):
    db = connection[dbname] 
    #print 'insert data:',para
#    print para.keys()
#    print 'user_id:',para['user_id']
    print 'is_open:',para['is_open']
    url=para['url']
    res=db.post.find_one({'url':url})

    if res:
        if para['is_open'] == 0:
            print "发现了一个被删掉的帖子 %s"%para['url']
            db.post.update({'url':url},{'$set':{'reply':para['reply'],
                                             'is_open':para['is_open'],
                                             'find_time':para['find_time'],
                                             }})
        else:
            print "发现了一个已经存在的帖子 但没被删除 更新其内容 %s"%para['url']
            db.post.update({'url':url},{'$set':{'reply':para['reply'],
                                             'is_open':para['is_open'],
                                             'content':para['content'],
                                             }})
            
        print 'this %s post have existed !'%url
    elif para['content']:     
        db.post.insert(para)
        print 'insert data success!!'

    print '='*50+'\n\n'



def transtime(stime):
    """
            将'11-12-13 11:30'类型的时间转换成unixtime
    """
    if stime and ':' in stime:
        res=stime.split(' ')
        year,mon,day=[int(i) for i in res[0].split('-')]
        hour,second=[int(i) for i in res[1].split(':')]
        unixtime=mktime(datetime.datetime(year,mon,day,hour,second))
        return unixtime
    else:
        return int(time.time())
    
def get_kds_post():
    root="http://club.pchome.net/"
    mainurl="http://club.pchome.net/forum_1_15.html"
    html=get_html(mainurl)
    if html:
        soup = BeautifulSoup(html,fromEncoding='gbk')
        #soup = BeautifulSoup(html)
        posts=soup.findAll('li',{'class':'i2'})
        #print 'post:',posts
        for p in posts:
            p_li=p.findAll('span')
            p_a=p.findAll('a')
            for a in  p_li:
                print a
            for a in  p_a:
                print a
            post_info={
            'url':p_li[1].a['href'][1:],
            'title':smart_str(p_li[1].a['title']),
            'reply':int(p_li[0].text),
            'user_id':int(p_a[-1]['bm_user_id']),
            'user_name':p_a[-1].text,
            'create_time':transtime(p_li[3].text),
            'find_time':time.time(),
            'is_open':1,
            'content':'',
            'is_check':0,
            'click':0,
            }
            print post_info
            post_url=str(os.path.join(root,post_info['url']))
            print 'post_url:',post_url
            post_html=get_html(post_url)
            if post_html is None:
                print ">"*150
                print "下载帖子html失败"
                print ">"*150
                continue
            if 'backHome' in post_html :
                post_info['is_open'] = 0
                post_info['find_time'] =time.time()
            else:
                post_soup = BeautifulSoup(post_html,fromEncoding='gbk')
                post_info['content'] = get_kds_post_reply(post_soup) 
                post_info['find_time'] =post_info['create_time']
            print 'post_info:',post_info
            post_insert(post_info,'kds')

    else:
        print 'get kds mainpage html fail'


def get_kds_post_reply(post_soup):
    """
    获取帖子的回帖
    """
    #post_html = get_html(url)
    #post_soup = BeautifulSoup(post_html,fromEncoding='gbk')

    #帖子封面图
    layer = 0
    reply_data = []
    reply_list =post_soup.find('div',{'id':'detail-content'}) 
    for reply in reply_list:
        if type(reply) == type(reply_list):
            #print '>'*90
            #print '%s楼'%layer
            author = reply.find('div',{'class':'author'})
            p_time = reply.find('div',{'class':'p_time'})
            #print 'user name:',author.a.strong.text
            #print 'user id:',author.a['bm_user_id']
            #print 'create_time:',p_time.text[-19:]
            m = reply.find('div',{'class':'mc'})
            m = m.div
            content = m.contents
            #print 'div:',m
            db_text = ''
            text_template = "%s<br>"
            img_template = """<img src="%s"></img>"""
            for text in content:
                #print 'text:',text
                if text == u'\n':
                    continue
                elif type(text) == type(m):
                    if text.name == 'a' and text.img and text.img.get('onload',None):
                        #print 'img:',text.img['src']
                        db_text += img_template%text.img['src']
                else:
                    #print 'reply:',text
                    db_text += text_template%text
                    
                #print "db_text:",db_text
            reply_info = {'user_name':author.a.strong.text,
                          'user_id':author.a['bm_user_id'],
                          'content':db_text,
                          'create_time':p_time.text[-19:],
            }
            reply_data.append(reply_info)
            #print 'reply_info:',reply_info
            layer +=1
    return reply_data
                
def get_tieba_post(tieba_name='liyi'):
    """
    抓取百度贴白有些的帖子地址
    """
    url = "http://tieba.baidu.com/f?kw=%s"%tieba_name
    tieba_url_root = "http://tieba.baidu.com"
    tieba_html = get_html(url)

    if tieba_html:
        soup = BeautifulSoup(tieba_html,fromEncoding='gbk')
        thread_list = soup.find('ul',{'id':'thread_list'})
        #print 'thread_list:',thread_list
        post_list = thread_list.findAll('li',{'class':'j_thread_list clearfix'})
        #print "post_list:",len(post_list)
        for p in post_list[2:]:
            #print '===================================\n'
            #print 'row:',p
            time.sleep(3)
            div_title = p.find('a',{'class':'j_th_tit'})
            title_text = div_title.text
            org_title = title_text.encode('utf-8')
            filter_title = gfw.replace(org_title)
            if org_title != filter_title:
                print 'title_text:',title_text
                print '>>>>>>>>>>>>>>>>>>>>>>>>>>>发现不和谐帖子!!!!!!!!!!!!!!!!!<<<<<<<<<<<<<<<<<<<<<<<<<<'
                continue
            #print "title:",div_title
            div_author = p.find('div',{'class':'threadlist_author'}).span.a
            #print "author:",div_author
            div_reply = p.find('div',{'class':'threadlist_rep_num'})
            #print "reply:",div_reply
            url = div_title['href'][1:]
            post_url=str(os.path.join(tieba_url_root,url))
            #print "post_url:",post_url
            if div_author is not None:
                #print "author:",div_author.text
                author = div_author.text
            else:
                author = 'diaosi'
            #print "reply:",div_reply.text
            post_info = {
            'url':int(url[2:]),
            'title':title_text,
            'reply':int(div_reply.text),
            'user_name':author,
            'user_id':'',
            'create_time':time.time(),
            'is_open':1,
            'content':[],
            'is_check':0,
            'click':0,
            'find_time':time.time(),
            'tieba_name':tieba_name,
            }
            post_html = get_html(post_url)
            if post_html is None:
                print ">"*150
                print "下载帖子html失败"
                print ">"*150
                continue
            #reply_list = post_soup.findAll('div',{'class':'p_post'})
            #print 'reply_len:',len(reply_list)
            #if len(reply_list) < 1 :
            if 'closeWindow' in post_html :
                post_info['is_open'] = 0
                post_info['find_time'] =int(time.time())
            else:
                """
                获取帖子总页数
                page_line = post_soup.findAll('li',{'class':'l_pager pager_theme_2'})
                if page_line:
                    last_page = int(page_line[0].findAll('a')[-1]['href'].split('=')[-1])
                    print 'last_page:',last_page
                else:
                    last_page =1
                    print 'just one page this post'
                """
                post_info['content'] = get_tieba_reply(post_html,sort_name=tieba_name)
                #print 'post_info:',post_info
                create_time = post_info['content'][0]['create_time'] 
                post_info['create_time'] = create_time
                post_info['find_time'] = time.time()
                post_html2 = get_html(post_url+'?pn=2')
                #下载第二页
                if post_html2 is not None and 'closeWindow' not in post_html:
                    next_content = get_tieba_reply(post_html2,sort_name=tieba_name,page=2)
                    if next_content:
                        post_info['content'].extend(next_content)
                    post_html3 = get_html(post_url+'?pn=3')
                    #下载第三页
                    if post_html3 is not None and 'closeWindow' not in post_html:
                        next_content = get_tieba_reply(post_html3,sort_name=tieba_name,page=3)
                        if next_content:
                            post_info['content'].extend(next_content)
                        post_html4 = get_html(post_url+'?pn=4')
                        #下载第四页
                        if post_html4 is not None and 'closeWindow' not in post_html:
                            next_content = get_tieba_reply(post_html4,sort_name=tieba_name,page=4)
                            if next_content:
                                post_info['content'].extend(next_content)
            #print 'post info:',post_info
            post_insert(post_info,'baidu')


    else:
        print 'get tieba mainpage html fail'

def get_tieba_reply(post_html,sort_name,page=1):
    """
    解析帖子内容
    """
    post_soup = bs4(post_html,fromEncoding='gbk')
    db_name = 'tieba'
    tieba_reply = tieba.reply
    reply_list = post_soup.find_all('div',class_='l_post')
    #print 'reply list lenght:',len(reply_list)
    rcount = 1
    reply_data = []
    author_name = '' 
    #print reply_list
    new_reply_list = []
    author_name = ''
    for reply in reply_list:
        #print '>'*150
        #print reply
        if reply is None :
            continue
        #print 'reply:',reply
        reply_data = json.loads(reply['data-field'])
        #print reply_data
        floor = reply_data['content']['floor']
        #print '第%s楼'%floor
        user_name = reply.find({'li':{'class':'d_name'}}).a.img['username']
        create_time = reply_data['content']['date']
        user_id = reply_data['author']['id']
        #print 'create_time:',create_time
        if rcount == 1:
            author_name = user_name
        rcount+=1
        #print user_name
        content = reply.find_all('cc')
        if content:
            content = content[0]
        else:
            continue
        #print 'cc:',content
        elements = content.div.contents
        if elements:
            new_elements = {'reply_content':[]}
            for e in elements[:10]:
                #print 'e:',e,type(e)
                if isinstance(e,Tag):
                    #对图片做转存
                    if e.name == 'img':
                        #只存楼主的图
                        if user_name == author_name:
                            new_e = {'tag':'img','content':e['src']}
                        else:
                            continue
                    else:
                        new_e = {'tag':e.name,'content':e.string}
                else:
                    new_e = {'tag':'p','content':e.string}
                if new_e['content']:
                    new_elements['reply_content'].append(new_e)
            
            new_elements['create_time'] = transtime(create_time)
            new_elements['user_name'] = user_name 
            new_elements['user_id'] = user_id 
            #print 'new elements:',new_elements
            new_reply_list.append(new_elements)
        else:
            continue
    #print 'new reply list:',new_reply_list
    return new_reply_list

def check_filter_title():
    post_list=tieba.post.find({'is_open':0},limit=50,skip=0,sort=[('find_time',DESCENDING)])
    for p in post_list:
        t = p['title'].encode('utf-8')
        ft = gfw.replace(t)
        print 'url:%s, title:%s,  filter_title:%s   if in :%s'%(p['url'],t,ft,str(ft == t))

def get_tieba_info(tieba_name='liyi'):
    """
    获取贴吧某个吧信息
    """
    db =  connection['tieba']
    post = db.post
    img = db.img
    print '===========================%s info================================='%tieba_name
    print 'total post count:',post.count()
    print 'delete post count:',post.find({'is_open':0,'tieba_name':tieba_name}).count()
    print 'open post count:',post.find({'is_open':1,'tieba_name':tieba_name}).count()
    print 'hexie post count:',post.find({'is_open':-1,'tieba_name':tieba_name}).count()
    print 'img count:',img.find({'type_name':tieba_name}).count()
    print '===================================================================='


if __name__ == "__main__":
    #if sys.argv[1] == 'test':
    #    get_tieba_info()
    #elif sys.argv[1] == 'kds':
    #    while True:
    #        try:
    #            get_kds_post()
    #        except Exception,e:
    #            print('\n'*9)
    #            traceback.print_exc()
    #            print('\n'*9)
    #else:
    #    while True:
    #        try:
    #            get_tieba_post("liyi")
    #            get_tieba_post("liyi")
    #            get_tieba_post("liyi")
    #            get_tieba_post("liyi")
    #            get_tieba_post("liyi")
    #            #get_tieba_post_img(u"姐脱")
    #        except Exception,e:
    #            print('\n'*9)
    #            traceback.print_exc()
    #            print('\n'*9)


    #html = get_html("http://tieba.baidu.com/p/2869738895")
    #print get_tieba_reply(html,'liyi','2869738895')
    
     
    get_tieba_post("liyi")
    get_tieba_post("liyi")
    get_tieba_post("liyi")
    get_tieba_post("liyi")
    get_tieba_post("liyi")

    #get_tieba_info()
    #get_tieba_post("jietup")
    #get_tieba_post("liyi")
    #get_tieba_post_img("jietup")
