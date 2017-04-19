# /usr/bin/env python
# -*- coding: utf-8 -*-
import qiniu.io
import qiniu.conf
import qiniu.rs
import qiniu.rsf
import qiniu.fop
import os.path
import settings
import sys
import random
import os
import os.path
import logging
#import mdb
import json
import requests
import StringIO
import pycurl
import time
import traceback
import string
from utils.chars import *
import mdb
from bson.objectid import ObjectId


current_path = os.path.split(os.path.realpath(__file__))[0]

client = requests.Session()
headers = {
           #'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:27.0) Gecko/20100101 Firefox/27.0',
           #'Referer':'http://tieba.baidu.com/p/2931020380',
           #'Accept':'image/png,image/*;',
           #'Host':' imgsrc.baidu.com',
           }

mktime=lambda dt:time.mktime(dt.utctimetuple())

class mdump(JSONEncoder):
    def default(self, obj, **kwargs):
        if isinstance(obj, ObjectId):
            return str(obj)
        else:
            return JSONEncoder.default(obj, **kwargs)

def dumps(data):
    """
    json dumps
    """
    res = json.dumps(data,cls=mdump)
    return res

def get_html(url,referer ='',verbose=False,protocol='http'):
    if not url.startswith(protocol):
        url = protocol+'://'+url
    url = str(url)
    print '============================================'
    print 'url:',[url]
    print '============================================'
    time.sleep(1)
    html=''
    headers = ['Cache-control: max-age=0',]
    try:
        crl = pycurl.Curl()
        crl.setopt(pycurl.VERBOSE,1)
        crl.setopt(pycurl.FOLLOWLOCATION, 1)
        crl.setopt(pycurl.MAXREDIRS, 5)
        crl.setopt(pycurl.CONNECTTIMEOUT, 8)
        crl.setopt(pycurl.TIMEOUT, 30)
        crl.setopt(pycurl.VERBOSE, verbose)
        crl.setopt(pycurl.MAXREDIRS,15)
        crl.setopt(pycurl.USERAGENT,'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:9.0.1) Gecko/20100101 Firefox/9.0.1')
        #crl.setopt(pycurl.HTTPHEADER,headers)
        if referer:
            crl.setopt(pycurl.REFERER,referer)
        crl.fp = StringIO.StringIO()
        crl.setopt(pycurl.URL, url)
        crl.setopt(crl.WRITEFUNCTION, crl.fp.write)
        crl.perform()
        html=crl.fp.getvalue()
        crl.close()
    except Exception,e:
        print('\n'*9)
        traceback.print_exc()
        print('\n'*9)
        return None
    return html

def get_html2(url):
    res =  mdb.httpclient.get(url)
    if res.status_code != 200:
        return None
    else:
        return res.content


def imgurl(key,space='',pformat=''):
    if not space:
        space = settings.get('tieba_img_host')
    pic_host = space
    return os.path.join(pic_host,key)+pformat

def imgurl2(key,space='',pformat=''):
    if not space:
        space = settings.get('tieba_img_host')
    pic_host = space
    return os.path.join(pic_host,key)+pformat

def random_key(key_amount,key_len=12):
    """
    生成激活码
    """
    key_list = set()
    key_chars = string.lowercase+string.digits
    #logging.info('key_chars:%s'%key_chars)
    for i in xrange(key_amount):
        random_char_list = [random.choice(key_chars) for i in range(key_len)]
        key_list.add(''.join(random_char_list))
    if key_amount == 1:
        return key_list.pop()
    return key_list

def save_local_img(key,data,root=''):
    if not root:
        root = settings.get("photo_path")
    folder = key[-1]
    folder_path = os.path.join(root,folder)
    file_path = os.path.join(root,folder,key)
    print 'file_path:',file_path
    if os.path.exists(file_path):
        return
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    f = open(file_path, "wb")
    f.write(data)
    f.close()

def get_uptoken(space = 'tieba'):
    """
    获取七牛上传token
    """
    policy = qiniu.rs.PutPolicy(space)
    uptoken = policy.token()
    #print 'uptoken:',uptoken
    return uptoken

def upload_file(pic_name,name='',local="test"):
    """
    上传图片
    """
    local = os.path.join(current_path,local,pic_name)
    if not name:
        name = os.path.split(pic_name)[-1]
    #print 'space:',settings.get('petimg_space')
    #print 'name:',name
    #print 'local:',local
    ret, err = qiniu.io.put_file(get_uptoken(settings.get('petimg_space')),name, local)
    print 'ret:',ret
    print 'err:',err
    return ret

def update_web_file(web_url,name,bucket_name=''):
    """
    """
    global client,headers
    if not bucket_name:
        bucket_name=settings.get('tieba_img_bucket')
    uptoken = get_uptoken(bucket_name)
    extra = qiniu.io.PutExtra()
    extra.mime_type = "image/jpeg"

    #r = client.get(web_url,headers=headers)
    r = get_html(web_url,referer='http://tieba.baidu.com/p/2931020380')
    data = StringIO.StringIO(r)
    #print 'file size:',data.len
    save_local_img(name,r)
    ret, err = qiniu.io.put(uptoken,name,data,extra)
    data.close()
    if ret:
        ret['fsize'] = data.len
        return ret
    else:
        sys.stderr.write('error: %s ' % err)
        return err


def qiniu_img_info(key,bucket_name=''):
    """
    获取七牛图片信息
    """
    if not bucket_name:
        bucket_name = settings.get('tieba_img_bucket') 
    ret, err = qiniu.rs.Client().stat(bucket_name, key)
    return ret,err

def dumps(data):
    res = json.dumps(data,cls=mdump)
    return res

def clean_post():
    """
    清理垃圾帖子
    """
    post_list = mdb.baidu.post.find()
    for p in post_list:
	print "[url]%s==================="%p['url']
	print "[title]%s"%p['title']
        cover_img = p.get('post_cover_img','')
        if cover_img:
            res,err = qiniu_img_info(cover_img)
            if res:
                if res['fsize'] > 10240:
                    hash_exist = mdb.baidu.post.find_one({'cover_hash':res['hash']})
                    if not hash_exist:
                        mdb.baidu.post.update({'_id':p['_id']},{'$set':{'cover_hash':res['hash']}})
                        print u"[clean]好帖子"
                        continue
                    else:
                        print u"[clean]删除封面已经存在的帖子"
                else:
                    print u"[clean]删除封面图片太小的帖子"
            else:
                print u"[clean]删除封面图片不存在帖子"
        else:
            print u"[clean]删除没封面的帖子"
        mdb.baidu.post.remove({'_id':p['_id']})

def download_img():
    """
    下载所有的图片
    """
    pass

def list_all(bucket, rs=None, prefix=None, limit=None):
    count = 0
    if rs is None:
        rs = qiniu.rsf.Client()
    marker = None
    err = None
    s = requests.Session()
    #while err is None and count<10:
    while err is None :
        ret, err = rs.list_prefix(bucket, prefix=prefix, limit=limit, marker=marker)
        marker = ret.get('marker', None)
        for item in ret['items']:
            post_id = item['key'].split('_',1)[0]
            print 'post_id:',post_id
            if len(post_id) < 20:
                continue 
            post_info = mdb.baidu.post.find_one({'_id':ObjectId(post_id)})
            if  not post_info:
                print '帖子已经被删了'
                qiniu.rs.Client().delete(bucket,item['key'])
                continue
            try:
                print 'img info:',item
                if item.get('fsize',0) < 10240:
                    print '删图太小的图片'
                    qiniu.rs.Client().delete(bucket,item['key'])
                else:
                    print '发现需要保存的图片'
                    img_url = "http://tiebaimg.qiniudn.com/"+item['key']
                    img_data = s.get(img_url).content 
                    f = open("%s/%s"%("share",item['key']), "wb")
                    f.write(img_data)
                    f.close()
            except Exception,e:
                continue
        count+=limit
    if err is not qiniu.rsf.EOF:
        # 错误处理
        pass
    print "count:",count

def list_pic():
    s = requests.Session()
    post_list = mdb.baidu.post.find()
    print 'post_count:',mdb.baidu.post.count()
    for post in post_list:
        for r in post["content"]:
            for c in r['reply_content']:
                if c['tag'] == 'img':
                    try:
                        #item = qiniu_img_info(c['key'])
                        #print 'img info:',item

                        print '发现需要保存的图片'
                        img_url = "http://tiebaimg.qiniudn.com/"+c['content']
                        img_data = s.get(img_url).content 
                        root = settings.get('photo_path')
                        folder = c["content"][-1]
                        folder_path = os.path.join(root,folder)
                        file_path = os.path.join(root,folder,c['content'])
                        print 'file_path:',file_path
                        if os.path.exists(file_path):
                            print '>>文件已经存在'
                            continue
                        else:
                            img_url = "http://tiebaimg.qiniudn.com/"+c['content']
                            img_data = s.get(img_url).content 
                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)
                        f = open(file_path, "wb")
                        f.write(data)
                        f.close()
                    except Exception,e:
                       traceback.print_exc() 




if __name__ == '__main__':
    pass
    mdb.init()
    web_url = "http://images.cnitblog.com/blog/234895/201311/30212303-9ea9d82b964b425d8c46eea51fc3bf77.x-png"
    #print update_web_file(web_url,'pppp1',settings.get('tieba_img_bucket'))
    #print imgurl('test2')
    #print qiniu_img_info('3p1.jpg','tiebaimg')
    #print qiniu_img_info('537040d91d41c867b6a2a813_grjxzpwi93t475n8bs8srf7a')
    #clean_post()
    #r = requests.get(web_url)
    #save_local_img('test',r.content)
    print '--'
    print get_uptoken(space = 'petimg')
    print '--'
