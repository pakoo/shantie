#! /usr/bin/env python
# -*- coding: utf-8 -*-
#Author:pako
#Email:zealzpc@gmail.com
"""
some db interface 
"""
from config import *
import datetime
con = mdb.con
import logging

######################db.init######################
gfw = GFW()
gfw.set(open(os.path.join('keyword.txt')).read().split('\n'))

def update_post(url,db,content=None,is_open=1):
    if is_open ==0 :
        con[db].post.update({'url':url},{'$set':{'is_open':is_open,'find_time':time.time(),'last_click_time':time.time()}})
    else:
        con[db].post.update({'url':url},{'$set':{'is_open':is_open,'find_time':time.time(),'last_click_time':time.time()}})
        
"""
def kds_review():
    db = con['kds']
    yesterdat=time.time()-48*3600
    #yesterdat=time.time()-100
    old_post=db.post.find({'create_time':{'$lt':yesterdat},'is_open':1})
    #old_post=db.post.find({'is_open':1})
    #old_post=post.find({'is_open':1})
    logging.info('old post amount:%s'%old_post.count())
    root="http://club.pchome.net/" #root = "http://tieba.baidu.com/p/" try:
    try:
        for tiezi in old_post:
                post_url=str(os.path.join(root,str(tiezi['url'])))  
                post_html=get_html(post_url)
                if post_html is None:
                    continue
                #post_soup = BeautifulSoup(post_content_all,fromEncoding='gbk')
                #post_content=post_soup.find('div',{'class':'mc'})
                if 'backHome' in post_html:
                    logging.error( u'>>>>>>>>>>>>>>>>发现了一个被删除的帖子(%s)!<<<<<<<<<<<<<<<<<<<<'%post_url)
                    update_post(url = tiezi['url'],db='kds',is_open=0)   
                else:
                    logging.info('>>>>>>>>>>>>>>>>删除了已经存在了48h的帖子%s !<<<<<<<<<<<<<<<<<<<<'%tiezi['url'])
                    db.post.remove({'url':tiezi['url']}) 
    except Exception,e:
        traceback.print_exc() 
        pass
"""

def save_post_img(post_id):
    """
    保存帖子的图片去七牛
    """
    content = []
    post_cover_img = ''
    post_info = mdb.baidu.post.find_one({'url':post_id})
    need_reset = False
    if post_info:
        for r in post_info['content']:
            reply_content = []
            for e in r['reply_content']:
                if e['tag'] == 'img':
                    img_key = '%s_%s'%(str(post_info['_id']),tools.random_key(1,24))
                    #tools.update_web_file(e['content']+'?kilobug',img_key)
                    tools.update_web_file(e['content'],img_key)
                    e['old_content'] = e['content']
                    e['content'] = img_key
                    need_reset = True
                    if not post_cover_img:
                        post_cover_img = img_key
                reply_content.append(e)
            content.append(r)
        if need_reset:
            logging.warning('>>>>>>>>>>>>>reset baidu post %s content '%post_info['url'])
            mdb.baidu.post.update({'_id':post_info['_id']},{'$set':{'content':content,'post_cover_img':post_cover_img}})



def tieba_review(dbname):
    db = con[dbname]
    #yesterdat=time.time()-48*3600
    yesterdat=time.time()-100
    old_post=db.post.find({'create_time':{'$lt':yesterdat},'is_open':1,'tieba_name':'liyi'})
    #old_post=con[dbname].post.find({'is_open':1})
    logging.info('old post amount:%s'%old_post.count())
    root = "http://tieba.baidu.com/p/"
    #try:
    for tiezi in old_post:
            post_url=os.path.join(root,str(tiezi['url']))  
            post_content_all=tools.get_html(post_url)
            if not post_content_all:
                continue
            if 'closeWindow' in post_content_all :
                org_title= tiezi['title'].encode('utf-8')
                filter_title = gfw.replace(org_title)
                print type(filter_title),len(filter_title)
                print type(tiezi['title']),len(tiezi['title'])
                logging.warning(u'filter_title:%s'%filter_title.decode('utf-8'))
                logging.warning(u'title:%s'%tiezi['title'])
                if filter_title.decode('utf-8') != tiezi['title']:
                    logging.warning( u'>>>>>>>>>>>>>>>>发现了一个被删除的帖子(%s)! 现在删除<<<<<<<<<<<<<<<<<<<<'%post_url)
                    #update_post(url = tiezi['url'],db=dbname,is_open=0)   
                    #save_post_img(tiezi['url'])
                    db.post.remove({'url':tiezi['url']}) 
                else:
                    logging.error( u'>>>>>>>>>>>>>>>>发现了一个被删除的帖子(%s)!<<<<<<<<<<<<<<<<<<<<'%post_url)
                    update_post(url = tiezi['url'],db=dbname,is_open=0)   
                    save_post_img(tiezi['url'])
            else:
                logging.info('>>>>>>>>>>>>>>>>删除了已经存在了48h的帖子%s !<<<<<<<<<<<<<<<<<<<<'%tiezi['url'])
                db.post.remove({'url':tiezi['url']}) 
                #update_post(url = tiezi['url'],db=dbname,is_open=0)   
                #save_post_img(tiezi['url'])
                    
    #except Exception,e:
    #    traceback.print_exc() 
    #    pass

def upload_close_post():
    post = mdb.baidu.post.find({'is_open':0})
    for p in post:
        save_post_img(p['url'])


if __name__ == "__main__":
    mdb.init()
    upload_close_post()
    #while True:
    #    try:
    #        tieba_review('tieba')
    #        kds_review()
    #        time.sleep(600)
    #    except Exception,e:
    #        print('\n'*9)
    #        traceback.print_exc()
    #        print('\n'*9)
    #save_post_img(2869772495)
    #print tieba_review('tieba')
    #tieba_review('baidu')
    

    #update_post({'url':"thread_1_15_6890043__.html",'is_open':0})
