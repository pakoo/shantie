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
import app
from bson.objectid import ObjectId
import jiguang
import json


def transUinxtime2Strtime(utime,type=0):
    if type==0:
        stime=time.strftime("%Y-%m-%d %H:%M",time.localtime(utime))
        return stime
    elif type==1:
        stime=time.strftime("%m.%d",time.localtime(utime))
        return stime

def get_real_reply(elements,use_qiniu=True):
    """
    将字典数据转为html
    """
    new_elements = []
    #print 'elements:',elements
    for e in elements:
        if e['tag'] == 'img':
            #是否使用七牛的图片
            if use_qiniu:
                new_e = '<img src="%s" class="img-responsive">'%tools.imgurl(e['content'],pformat='-post')
            else:
                new_e = '<img src="%s" class="img-responsive">'%(e.get('old_content','') or e.get('content','')+"?kilobug") 
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
    res = mdb.baidu.post.find({'is_open':settings.get('post_flag'),'post_cover_img':{'$exists':True}},sort=[('last_click_time',-1)],limit=6,fields={'_id':False,'url':True,'post_cover_img':True,'title':True})
    for p in res:
        p['post_cover_img'] = tools.imgurl(p['post_cover_img'],pformat='-cover300')
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
        """
        pid = int(self.get_argument('pid'))
        old_post_info=get_old_tieba_post_reply(pid)
        hots = get_hot_post()
        if old_post_info: 
            logging.warning("%s is an old post!"%pid)
            self.render('old_post.html',data=old_post_info,tieba=True,hots=hots)
            mdb.tieba.post.update({'url':pid},{'$set':{'last_click_time':time.time()},'$inc':{'click':1}})
        else:
            logging.warning("%s is a new post!"%pid)
            post_info = mdb.baidu.post.find_one({'url':pid})
            if not post_info:
                self.redirect('/newpost')
                return
            self.render('post.html',post=post_info,u2s =transUinxtime2Strtime,tr=get_real_reply,hots=hots)
            mdb.baidu.post.update({'url':pid},{'$set':{'last_click_time':time.time()},'$inc':{'click':1}})

class PostJson(BaseHandler):
    """
    用户
    """
    def get(self):
        """
        创建用户页面
        """
        post_id = is_oid(self.get_argument('post_id'))
        #old_post_info=get_old_tieba_post_reply(pid)
        #hots = get_hot_post()
        #if old_post_info: 
        #    logging.warning("%s is an old post!"%pid)
        #    self.render('old_post.html',data=old_post_info,tieba=True,hots=hots)
        #    mdb.tieba.post.update({'url':pid},{'$set':{'last_click_time':time.time()},'$inc':{'click':1}})
        #else:
        #logging.warning("%s is a new post!"%pid)
        post_info = mdb.baidu.post.find_one({'_id':ObjectId(post_id)})
        for c in post_info['content']:
            for r in c['reply_content']:
                if r['tag'] == 'img':
                    r['content'] = tools.imgurl(r['content'],pformat='-post')
        self.finish(tools.dumps(post_info))
        mdb.baidu.post.update({'_id':ObjectId(post_id)},{'$set':{'last_click_time':time.time()},'$inc':{'click':1}})




class HotPostList(BaseHandler):
    """
    帖子列表
    """
    def get(self):
        """
        """
        page = int(self.get_argument('page',1))
        count = 20
        post_list = []
        res = mdb.baidu.post.find({'is_open':settings.get('post_flag')},sort=[('last_click_time',-1)],skip=(page-1)*count,limit=count)
        for p in res:
            p['abstract'] = get_post_abstract(p)
            if p.get('post_cover_img'):
                p['post_cover_img'] = tools.imgurl2(p['post_cover_img'],pformat='-cover300')
            else:
                p['post_cover_img']=''
            post_list.append(p)
        self.render("hot_post_list.html",posts = post_list,page = page)

class PostList(BaseHandler):
    """
    帖子列表
    """
    def get(self):
        """
        """
        page = int(self.get_argument('page',1))
        count = 20
        post_list = []
        res = mdb.baidu.post.find({'is_open':settings.get('post_flag')},sort=[('find_time',-1)],skip=(page-1)*count,limit=count)
        for p in res:
            p['abstract'] = get_post_abstract(p)
            if p.get('post_cover_img'):
                p['post_cover_img'] = tools.imgurl(p['post_cover_img'],pformat='-cover300')
            else:
                p['post_cover_img']=''
            post_list.append(p)
        self.render("post_list.html",posts = post_list,page = page)

class PostListJson(BaseHandler):
    """
    帖子列表json
    """
    def get(self):
        page = int(self.get_argument('page',1))
        count = 30
        post_list = []
        res = mdb.baidu.post.find({'is_open':0,'post_cover_img':{'$exists':True}},sort=[('last_click_time',-1)],skip=(page-1)*count,limit=count,fields={'title':True,'post_cover_img':True})
        for p in res:
            #p['abstract'] = get_post_abstract(p)
            if p.get('post_cover_img'):
                p['post_cover_img'] = tools.imgurl(p['post_cover_img'],pformat='-cover300')
            else:
                p['post_cover_img']=''
            p['post_id'] = p['_id']
            p.pop('_id')
            post_list.append(p)
        self.finish(tools.dumps({'post_list':post_list}))

class HotPostListJson(BaseHandler):
    """
    帖子列表json
    """
    def get(self):
        page = int(self.get_argument('page',1))
        count = 30
        post_list = []
        res = mdb.baidu.post.find({'is_open':0,'post_cover_img':{'$exists':True}},sort=[('find_time',-1)],skip=(page-1)*count,limit=count,fields={'title':True,'post_cover_img':True})
        for p in res:
            #p['abstract'] = get_post_abstract(p)
            if p.get('post_cover_img'):
                p['post_cover_img'] = tools.imgurl(p['post_cover_img'],pformat='-cover300')
            else:
                p['post_cover_img']=''
            p['post_id'] = p['_id']
            p.pop('_id')
            post_list.append(p)
        self.finish(tools.dumps({'post_list':post_list}))

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

class FulituList(BaseHandler):
    """
    """
    def get(self):
        """
        """
        page = int(self.get_argument('page',1))
        data = [
                {'title':u'喷血推荐！最新流出川航空姐性爱门事件，淫语内容劲爆！','pic_list':['http://tiebaimg.qiniudn.com/kj1.jpg',"http://tiebaimg.qiniudn.com/kj2.jpg","http://tiebaimg.qiniudn.com/kj3.jpg"]},
                {'title':u'女神极限诱惑你.这身材这胸.哥快撸出血了','pic_list':['http://tiebaimg.qiniudn.com/ns1.jpg',"http://tiebaimg.qiniudn.com/ns2.jpg","http://tiebaimg.qiniudn.com/ns3.jpg"]},
                {'title':u'碉堡了,这几位妹子在干嘛，3P？？','pic_list':['http://tiebaimg.qiniudn.com/3p1.jpg',"http://tiebaimg.qiniudn.com/3p2.jpg","http://tiebaimg.qiniudn.com/3p3.jpg"]},
                {'title':u'最新爆出超美银行女职员与领导性爱高清视频！','pic_list':['http://tiebaimg.qiniudn.com/zy1.jpg',"http://tiebaimg.qiniudn.com/zy2.jpg","http://tiebaimg.qiniudn.com/zy3.jpg"]},
                {'title':u'南京地铁惊现中国版，伸手对包臀美妇又抠又摸','pic_list':['http://tiebaimg.qiniudn.com/nj1.jpg',"http://tiebaimg.qiniudn.com/nj2.jpg","http://tiebaimg.qiniudn.com/nj3.jpg"]},
                ]
        if page > 1:
            self.finish(json.dumps({'fuli_list':[]}))
        else:
            self.finish(json.dumps({'fuli_list':data}))

class ApkDownload(BaseHandler):
    """
    """
    def get(self):
        """
        """
        self.render('apk.html',version = settings.get('apk_version'))

class ApkDownload2(BaseHandler):
    """
    """
    def get(self):
        """
        """
        self.render('apk2.html',version = settings.get('apk_version'))

class ApkWXDownload(BaseHandler):
    """
    """
    def get(self):
        """
        """
        self.render('http://ostatic.qiniudn.com/fuliba%s.apk'%settings.get('apk_version'))

class LikePost(BaseHandler):
    """
    """
    def post(self):
        """
        """
        post_id = int(self.get_argument("post_id"))
        if post_id:
            mdb.baidu.post.update({'url':post_id},{'$set':{'last_like_time':time.time()},'$inc':{'like':1}})
            mdb.tieba.post.update({'url':post_id},{'$set':{'last_like_time':time.time()},'$inc':{'like':1}})
        self.finish("1")

class Index(BaseHandler):
    """
    """
    def get(self):
        """
        """
        self.redirect('/hotpost')

class OldPostUrl(BaseHandler):
    """
    """
    def get(self,pid):
        """
        """
        self.redirect('/post/tieba?pid=%s'%pid)

class OldList(BaseHandler):
    """
    """
    def get(self,pid=0):
        """
        """
        self.redirect('/hotpost')

class RemovePost(BaseHandler):
    """
    """
    def get(self):
        """
        """
        pid = int(self.get_argument("pid"))
        mdb.baidu.post.remove({'url':pid})
        mdb.tieba.post.remove({'url':pid})
        self.finish('1')


class HotAlbumJson(BaseHandler):
    """
    获取今天推荐的相册
    """
    def get(self):
        """
        """
        page = int(self.get_argument('page',1))
        album_list = mdb.baidu.post.find({'is_open':settings.get('post_flag'),'reply_img_count':{'$gt':2}},fields={'reply_img_list':True,'title':True,'_id':False},sort=[('find_time',-1)],skip=20*(page-1),limit=20)
        album_list = list(album_list)
        for idx,album in enumerate(album_list):
            pics = []
            for pic in album['reply_img_list']:
                pic = tools.imgurl(pic,pformat='-cover300') 
                #pic = tools.imgurl(pic) 
                pics.append(pic)
            album_list[idx]['pic_list'] = pics
            album_list[idx].pop('reply_img_list')

        self.finish(json.dumps({'fuli_list':album_list}))


class Yvideo(BaseHandler):
    """
    """
    def get(self,aid):
        print 'aid:',aid
        res = {}
        album_id = is_oid(aid)
        album_info = mdb.con.yy.album.find_one({'_id':ObjectId(album_id)})
        album_info['season'] = int(album_info['season'])
        print 'album_id:',album_id
        videos = mdb.con.yy.video.find({'album_id':ObjectId(album_id)})
        for v in videos:
            if res.get(v['season'],None):
                res[v['season']].append(v)
            else:
                res[v['season']] = [v]
        print 'videos:',videos.count()
        self.render("yvideo.html",data=res,album_info=album_info)

class Xiameiju(BaseHandler):
    """
    """
    def get(self,page):
        if not page:
            page=1
        page=int(page)
        print 'page:',page
        count = 100
        album = mdb.con.yy.album.find({},sort=[('create_time',-1)],skip=(page-1)*count,limit=count)
        self.render("yindex.html",videos=album,page=page)

#class YoLogin(YoHandler):
#
#    def get(self):
#        following_info = []
#        following_list = mdb.yocon.follow.find({'from':self._id})
#        for u in following_list:
#            res = mdb.yocon.user.find_one({'_id':u['to']})
#            following_info.append({'name':res['name'],'uid':u['to']})
#        self.sendline({'name':self.name,'uid':self.uid,'following_info':following_info})

#class YoNewUser(YoHandler):
#    """
#    注册用户
#    """
#    def get(self):
#        name = self.get_argument('user_name')
#        exist_name = mdb.yocon.user.find_one({'name':name})
#        exist_device = mdb.yocon.user.find_one({'device_id':self.yoid})
#        if exist_name or exist_device:
#            self.senderror(u'eixst user name',-2)
#        else:
#            uinfo = {
#                        '_id':ObjectId(),
#                        'name':name,    
#                        'device_id':self.yoid,    
#                        'register_ip':self.ip,    
#                        'create_time':time.time(),    
#                        'send_yo_count':0,    
#                        'receive_yo_count':0,    
#                        }
#            mdb.yocon.user.insert(uinfo)
#            #self.set_cookie('yoid','ycsb')
#            self.sendline({'uid':uinfo['_id']})
#
#class YoAddUser(YoHandler):
#    """
#    添加yo好友
#    """
#    def get(self):
#        to_user_name = self.get_argument('to_user_name')
#        to_user_info =  mdb.yocon.user.find_one({'name':to_user_name})
#        if to_user_info:
#            exist = mdb.yocon.follow.find_one({'from':self._id,'to':to_user_info['_id']})
#            if not exist:
#                mdb.yocon.follow.insert({
#                    'from':self._id,
#                    'to':to_user_info['_id'],
#                    'create_time':time.time(),
#                    })
#            self.sendline({'uid':to_user_info['_id'],'user_name':to_user_name})
#        else:
#            self.senderror(u'not this user')
#
#class YoPush(YoHandler):
#    """
#    yo push
#    """
#    def get(self):
#        to_uid = self.get_argument('to_uid')
#        msg_type = self.get_argument('msg_type',1)
#        jiguang.push(self.uid,to_uid,msg_type)
#        self.sendline()



class Application(tornado.web.Application):
    def __init__(self):

        app_settings={
            'debug':True,
            'template_path':"template",
        }

        self.manager_handlers = [
                ]
        handlers = [
            (r"/", app.weixin),
            (r'/index',Index),
            (r'/post/tieba',Post),
            (r'/liyi/post/([0-9]+)/?',OldPostUrl),
            (r'/tieba/post/([0-9]+)/?',OldPostUrl),
            (r'/liyi/([0-9]+)/?',OldList),
            (r'/liyi/?',OldList),
            (r'/tieba/([0-9]+)/?',OldList),
            (r'/tieba/?',OldList),
            (r'/newpost',PostList),
            (r'/hotpost',HotPostList),
            (r'/postlistjson',PostListJson),
            (r'/hotpostlistjson',HotPostListJson),
            (r'/postjson',PostJson),
            (r'/hotalbumjson',HotAlbumJson),
            (r'/oldpost',OldPostList),
            (r'/fulitu',FulituList),
            (r'/apk',ApkDownload),
            (r'/apk2',ApkDownload2),
            (r'/rp',RemovePost),
            (r'/likepost',LikePost),
            (r'/down.myapp.com/apk',ApkWXDownload),

            #(r'/yo_login',YoLogin),
            #(r'/yo_newuser',YoNewUser),
            #(r'/yo_adduser',YoAddUser),
            #(r'/yo_push',YoPush),


            #(r'/video/(\w{24})',Yvideo),
            #(r'/(\d{0,5})',Xiameiju),

            (r'/static/(.*)', tornado.web.StaticFileHandler, {"path": "static"}),
            #(r'/uploadfile/(.*)', tornado.web.StaticFileHandler, {"path": "share"}),



        ]
        handlers.extend(self.manager_handlers)
        #管理员可以访问的路径
        self.manager_path=[p[0] for p in self.manager_handlers]

        tornado.web.Application.__init__(self,default_host="xiameiju.net",handlers=handlers,**app_settings)


        self.add_handlers(r"weixin\.xiameiju\.net", [
        (r"/", app.weixin),
        (r"/livepic", app.LiveCityPic),
        (r"/mina25", app.mina25),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./static"}),
        ])

        self.add_handlers(r"www\.xiameiju\.net", [
        #(r"/", app.weixin),
        (r'/video/(\w{24})',Yvideo),
        (r'/(\d{0,5})',Xiameiju),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./static"}),
        ])


if __name__ == '__main__':
    mdb.init()
    jiguang.init_pusher()
    port = settings.get('server_port')
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    logging.info("starting [%s] webserver on 0.0.0.0:%d" % ('debug',port))
    http_server = tornado.httpserver.HTTPServer(request_callback=Application())
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

