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
import logging
import review_open_post
import mdb

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
            review_open_post.update_post(url=para['url'],db=dbname,is_open=0)
            review_open_post.save_post_img(para['url'])
            #db.post.update({'url':url},{'$set':{'reply':para['reply'],
            #                                 'is_open':para['is_open'],
            #                                 'find_time':para['find_time'],
            #                                 }})
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
    
                
def get_tieba_post(tieba_name='liyi'):
    """
    抓取百度贴白有些的帖子地址
    """
    url = "http://tieba.baidu.com/f?&kw=%s"%tieba_name
    tieba_url_root = "http://tieba.baidu.com"
    tieba_html = get_html(url)
    #print 'tieba_html:',tieba_html
    if tieba_html:
        #soup = bs4(tieba_html,from_encoding='gbk')
        soup = bs4(tieba_html)
        thread_list = soup.find('ul',{'id':'thread_list'})
        #print 'thread_list:',len(thread_list)
        #return
        post_list = thread_list.find_all('li',class_='j_thread_list clearfix')
        #print "post_list:",len(post_list)
        #print 'post:',post_list[-1]
        for p in post_list[2:]:
            print '===================================\n'
            #print 'row:',p
            time.sleep(3)
            div_title = p.find('a',{'class':'j_th_tit'})
            title_text = div_title.text
            #print 'title:',type(title_text),len(title_text)
            if len(title_text) <=5 :
                continue
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
            'today_like_count':0,
            }
            post_html = get_html(post_url+'?see_lz=1')
            if post_html is None:
                logging.error( ">"*150)
                logging.error( "下载帖子html失败")
                logging.error( ">"*150)
                continue
            #reply_list = post_soup.findAll('div',{'class':'p_post'})
            #print 'reply_len:',len(reply_list)
            #if len(reply_list) < 1 :
            if 'closeWindow' in post_html :
                continue
                #post_info['is_open'] = 0
                #post_info['find_time'] =int(time.time())
            else:
                post_info['content'],total_page,post_cover_img = get_tieba_reply(post_html,sort_name=tieba_name)
                #print 'post_info:',post_info
                print 'post_cover_img:',post_cover_img
                logging.info('%s 帖子总共有 %s页'%(post_info['url'],total_page))
                create_time = post_info['content'][0]['create_time'] 
                post_info['create_time'] = create_time
                post_info['find_time'] = time.time()
                if post_cover_img:
                    post_info['post_cover_img'] = post_cover_img
                else:
                    logging.warning(u"忽略没有封面的帖子")
                    continue

                page_turn = 3 if total_page > 4 else total_page -1
                if page_turn > 0:
                    for i in range(page_turn):
                        page_num= i+2
                        page_url = post_url+'?pn=%s&see_lz=1'%page_num
                        logging.info("开始下载第%s页 %s"%(page_num,page_url))
                        post_html = get_html(page_url)
                        if post_html is not None and 'closeWindow' not in post_html:
                            next_content,total_page,post_cover_img = get_tieba_reply(post_html,sort_name=tieba_name,page=page_num)
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
    post_soup = bs4(post_html)
    #获取帖子总页数
    total_page = int(post_soup.find('li',{'class':'l_reply_num'}).find_all('span')[-1].string)
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
    post_cover_img = ''
    for reply in reply_list:
        floor = 1
        #print '>'*150
        #print reply
        if reply is None :
            continue
        #print 'reply:',reply
        reply_data = json.loads(reply['data-field'])
        #print reply_data
        #print '第%s楼'%floor
        user_name = reply.find({'li':{'class':'d_name'}}).a.img['username']
        create_time = reply_data['content']['date']
        user_id = reply_data['author']['user_id']
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
            for e in elements:
                #print '*************************************\n'
                #print 'e:',e,type(e),e.name
                if isinstance(e,Tag):
                    #对图片做转存
                    if e.name == 'img':
                        #只存楼主的图
                        if user_name == author_name and 'static' not in e['src']:
                            post_cover_img = e['src']
                            new_e = {'tag':'img','content':e['src']}
                        else:
                            continue
                    else:
                        #print 'string:',e.string,type(e.string)
                        if e.string:
                            new_e = {'tag':e.name,'content':e.string.strip()}
                        else:
                            continue
                else:
                    new_e = {'tag':'p','content':e.string.strip()}
                if new_e['content'] and len(new_e['content']) > 2:
                    new_elements['reply_content'].append(new_e)
            new_elements['create_time'] = transtime(create_time)
            new_elements['user_name'] = user_name 
            new_elements['user_id'] = user_id 
            #print 'new elements:',json.dumps(new_elements)
            new_reply_list.append(new_elements)
        else:
            continue
        floor+=1
    #print 'new reply list:',new_reply_list
    return new_reply_list,total_page,post_cover_img

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

def get_yy_href(tag):
    url = ''
    if tag.get('thunderhref'):
        url = tag.get('thunderhref')
    elif tag.get('qhref'):
        url = tag.get('qhref')
    elif tag.get('href'):
        url = tag.get('href')

    site_name = tag.string
    return site_name,url


def get_yy_download_url(html,url):
    print 'url:',url
    #html = tools.get_html2(url)
    yyid = url.split('/')[-1]
    #soup = bs4(html,from_encoding='gbk')
    soup = bs4(html)
    season_list = soup.find_all('ul',class_='resod_list')
    #print 'season len:',len(season_list)
    info = soup.find_all('ul',class_='r_d_info')[0]
    cover_img = soup.find_all('div',class_='f_l_img')[0].find_all('img')[0]['src']
    album_name = soup.find_all('strong')[0].contents[0]
    #print 'cover_img:',cover_img
    #print 'info:',info
    print 'yyid:',yyid
    album= {'_id':ObjectId()}
    album['yyid'] = yyid
    album['cover_img'] =cover_img
    album['info'] =repr(info)
    album['season'] =len(season_list)
    album['create_time'] = time.time()
    album['name'] = album_name
    #print 'album_info:',album
    #mdb.yy.album.insert(album)
    for season in season_list:
        video_list=season.find_all('li')
        #print 'video len:',len(video_list)
        #print 'video season:',season['season']
        season_id = season['season']
        video_data = {'season':season_id,'video':[]}
        for video in video_list:
            #print '==================================================='
            data={'link':[],'album_id':album['_id']}
            video_format = video['format']
            video_id = video['itemid']
            data['item_id'] = video_id
            data['format'] = video_format
            data['album_name'] = album_name
            lks = video.find_all('div',class_="lks")[0]
            pks = video.find_all('div',class_="pks")
            download_links = pks[0].find_all('a')
            title = lks.find_all('a')[0]['title']
            data['title'] = title
            data['season'] = season_id
            for link in download_links:
                site_name,url = get_yy_href(link)
                data['link'].append({'name':site_name,'url':url})
            print 'data:',data
            #mdb.yy.video.insert(data)

def run_yy():
    """
    """
    root = "http://www.yyets.com/resource/%s"
    for i in range(23000):
        try:
            url = root%(10010+i)
            html = tools.get_html2(url)
            if not html:
                print '请求页面失败:',url
                html = tools.get_html2(url)
                if not html:
                    print '第二次请求页面失败:',url
                    continue
            elif '3*1000' in str(html):
                print '剧集不存在:',url
                continue
            get_yy_download_url(html,url)
            print '剧集存在:',url
            time.sleep(0.2)
        except Exception,e:
            print('\n'*9)
            traceback.print_exc()
            continue
            print('\n'*9)

            

if __name__ == "__main__":
    import json
    #run_yy()

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
    #            #get_tieba_post_img(u"姐脱")
    #        except Exception,e:
    #            print('\n'*9)
    #            traceback.print_exc()
    #            print('\n'*9)


    #html = get_html("http://tieba.baidu.com/p/3305591325")
    #print 'data:',json.dumps(get_tieba_reply(html,'liyi',1)[0])
    
    while True:
        try:
            get_tieba_post("liyi")
        except Exception,e:
            print('\n'*9)
            traceback.print_exc()
            print('\n'*9)
    
    #get_tieba_post("liyi")

    #get_tieba_info()
    #get_tieba_post("jietup")
    #get_tieba_post("liyi")
    #get_tieba_post_img("jietup")

