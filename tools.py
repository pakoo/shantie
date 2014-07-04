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


current_path = os.path.split(os.path.realpath(__file__))[0]

client = requests.Session()
headers = {
           #'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:27.0) Gecko/20100101 Firefox/27.0',
           #'Referer':'http://tieba.baidu.com/p/2931020380',
           #'Accept':'image/png,image/*;',
           #'Host':' imgsrc.baidu.com',
           }

mktime=lambda dt:time.mktime(dt.utctimetuple())

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
"""
def get_html(url):
    logging.info( '============================================')
    logging.info( 'url:%s'%url)
    logging.info( '============================================')
    time.sleep(1)
    html=''
    try:
        crl = pycurl.Curl()
        crl.setopt(pycurl.VERBOSE,1)
        crl.setopt(pycurl.FOLLOWLOCATION, 1)
        crl.setopt(pycurl.MAXREDIRS, 5)
        crl.setopt(pycurl.CONNECTTIMEOUT, 8)
        crl.setopt(pycurl.TIMEOUT, 30)
        crl.setopt(pycurl.MAXREDIRS,15)
        crl.setopt(pycurl.USERAGENT,'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:9.0.1) Gecko/20100101 Firefox/9.0.1')
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
"""

def imgurl(key,space=''):
    if not space:
        space = settings.get('tieba_img_host')
    pic_host = space
    return os.path.join(pic_host,key)+'?imageView/2/w/300/h/300/q/30/format/JPG'

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

def update_web_file(web_url,name):
    """
    """
    global client,headers
    bucket_name=settings.get('tieba_img_bucket')
    uptoken = get_uptoken(bucket_name)
    extra = qiniu.io.PutExtra()
    extra.mime_type = "image/jpeg"

    #r = client.get(web_url,headers=headers)
    r = get_html(web_url,referer='http://tieba.baidu.com/p/2931020380')
    data = StringIO.StringIO(r)
    ret, err = qiniu.io.put(uptoken,name,data,extra)
    data.close()
    if err is not None:
        sys.stderr.write('error: %s ' % err)
        return


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
            try:
                print 'img info:',item
                if item.get('fsize',0) < 10240:
                    qiniu.rs.Client().delete(bucket,item['key'])
                else:
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

if __name__ == '__main__':
    pass
    mdb.init()
    web_url = "http://imgsrc.baidu.com/forum/w%3D580/sign=9e20b6300db30f24359aec0bf894d192/d4550f2442a7d9332d3cf922af4bd11372f00135.jpg?kilobug"
    web_url2 = "http://imgsrc.baidu.com/forum/w%3D580/sign=f9ebe23596eef01f4d1418cdd0ff99e0/4f08f01f3a292df5ad9af744be315c6035a87368.jpg?kilobug"
    #update_web_file(web_url2,'lu1')
    #print imgurl('test2')
    #print qiniu_img_info('test2')
    #print qiniu_img_info('537040d91d41c867b6a2a813_grjxzpwi93t475n8bs8srf7a')
    #clean_post()
    list_all('tiebaimg',limit=500)
