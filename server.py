#/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
import tornado.template
import tornado.httpserver
import time
from BaseHandler import *
import requests
from datetime import datetime,timedelta
from collections import Counter
import settings
import mdb
import tools


def transUinxtime2Strtime(utime,type=0):
    if type==0:
        stime=time.strftime("%Y-%m-%d %H:%M",time.localtime(utime))
        return stime
    elif type==1:
        stime=time.strftime("%m.%d",time.localtime(utime))
        return stime

def get_real_reply(elements):
    """
    将字典数据转为html
    """
    new_elements = []
    #print 'elements:',elements
    for e in elements:
        if e['tag'] == 'img':
            new_e = '<img src="%s" class="img-responsive">'%tools.imgurl(e['content'])
        else:
            new_e = '<p>%s</p>'%e['content']
        new_elements.append(new_e)
    return ''.join(new_elements)

def get_post_abstract(post_info):
    """
    获取帖子的摘要
    """
    text = []
    content = post_info['content'][0]
    for e in content['reply_content']:
        if e['tag'] != 'img':
            text.append(e['content'])
    return ''.join(text)

def get_hot_post():
    """
    获取最火的3个帖子
    """
    hots = []
    res = mdb.baidu.post.find({'is_open':settings.get('post_flag'),'post_cover_img':{'$exists':True}},sort=[('last_click_time',-1)],limit=3,fields={'_id':False,'url':True,'post_cover_img':True,'title':True})
    for p in res:
        print p
        p['post_cover_img'] = tools.imgurl(p['post_cover_img'])
        hots.append(p)
    return hots

def get_old_tieba_post_reply(url):
    """
    获取帖子的内容
    """
    con = mdb.con
    dbname = 'tieba'
    is_open=settings.get('post_flag')
    tieba_url_root = "http://tieba.baidu.com/p"
    
    db_reply = con[dbname].post
    res = db_reply.find_one({'url':url,'is_open':0})
    if res:
        db_reply.update({'url':url},{'$inc':{'click':1}})
        db_reply.update({'url':url},{'$set':{'last_click_time':int(time.time())}})
        res['original_url'] = os.path.join(tieba_url_root,str(url))
        if res['content']:
            fcount = 1
            for reply in res['content']:
                #print 'reply:',reply
                if dbname == 'tieba':
                    reply['create_time'] = transUinxtime2Strtime(reply['create_time'])
                reply['floor'] = fcount
                fcount +=1
            if res.get('user_reply',None):
                for reply in res['user_reply']:
                    #print 'reply:',reply
                    if dbname == 'tieba':
                        reply['create_time'] = transUinxtime2Strtime(reply['create_time'])
                    reply['floor'] = fcount
                    fcount +=1
    return res

class Post(BaseHandler):
    """
    用户
    """
    def get(self):
        """
        创建用户页面
        """
        pid = int(self.get_argument('pid'))
        old_post_info=get_old_tieba_post_reply(pid)
        hots = get_hot_post()
        if old_post_info: 
            logging.warning("%s is an old post!"%pid)
            self.render('old_post.html',data=old_post_info,tieba=True,hots=hots)
            mdb.tieba.post.update({'url':pid},{'$set':{'last_click_time':time.time()},'$inc':{'clikc':1}})
        else:
            logging.warning("%s is a new post!"%pid)
            post_info = mdb.baidu.post.find_one({'url':pid})
            self.render('post.html',post=post_info,u2s =transUinxtime2Strtime,tr=get_real_reply,hots=hots)
            mdb.baidu.post.update({'url':pid},{'$set':{'last_click_time':time.time()},'$inc':{'clikc':1}})



class PostList(BaseHandler):
    """
    帖子列表
    """
    def get(self):
        """
        """
        page = int(self.get_argument('page',1))
        count = 30
        post_list = []
        res = mdb.baidu.post.find({'is_open':0},sort=[('find_time',-1)],skip=(page-1)*count,limit=count)
        for p in res:
            p['abstract'] = get_post_abstract(p)
            if p.get('post_cover_img'):
                p['post_cover_img'] = tools.imgurl(p['post_cover_img'])
            else:
                p['post_cover_img']=''
            post_list.append(p)
        self.render("post_list.html",posts = post_list,page = page)

class OldPostList(BaseHandler):
    """
    老帖子列表
    """
    def get(self):
        """
        获取老帖子列表
        """
        posts=[]
        page = int(self.get_argument('page',1))
        count = 50
        res = mdb.tieba.post.find({'is_open':settings.get('post_flag'),'tieba_name':'liyi'},{'url':1,'title':1,'find_time':1,'user_name':1,'click':1},limit=count,skip=count*(page-1),sort=[('find_time',-1)])
        for p in res:
            p['find_time'] = transUinxtime2Strtime(p['find_time'])
            posts.append(p)
        self.render('old_post_list.html',posts=posts,page=page)

class Index(BaseHandler):
    """
    """
    def get(self):
        """
        """
        self.redirect('/newpost')


class Application(tornado.web.Application):
    def __init__(self):

        app_settings={
            'debug':True,
            'template_path':"template",
        }

        self.manager_handlers = [
                ]
        handlers = [
            (r'/',Index),
            (r'/post/tieba',Post),
            (r'/newpost',PostList),
            (r'/oldpost',OldPostList),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {"path": "static"}),
            (r'/uploadfile/(.*)', tornado.web.StaticFileHandler, {"path": "share"}),
        ]
        handlers.extend(self.manager_handlers)
        #管理员可以访问的路径
        self.manager_path=[p[0] for p in self.manager_handlers]

        tornado.web.Application.__init__(self,handlers,**app_settings)


if __name__ == '__main__':
    mdb.init()
    port = settings.get('server_port')
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    logging.info("starting [%s] webserver on 0.0.0.0:%d" % ('debug',port))
    http_server = tornado.httpserver.HTTPServer(request_callback=Application())
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

