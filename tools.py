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

current_path = os.path.split(os.path.realpath(__file__))[0]

client = requests.Session()

mktime=lambda dt:time.mktime(dt.utctimetuple())

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

def imgurl(key,space=''):
    if not space:
        space = settings.get('tieba_img_host')
    pic_host = space
    return os.path.join(pic_host,key)

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
    global client
    bucket_name=settings.get('tieba_img_bucket')
    uptoken = get_uptoken(bucket_name)
    extra = qiniu.io.PutExtra()
    extra.mime_type = "image/jpeg"

    r = client.get(web_url)
    data = StringIO.StringIO(r.content)
    ret, err = qiniu.io.put(uptoken, name, data, extra)
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
    print ret


if __name__ == '__main__':
    pass
    web_url = "http://imgsrc.baidu.com/forum/w%3D580%3B/sign=3571403ff1deb48ffb69a1d6c0243b29/314e251f95cad1c86f0d26797d3e6709c93d513e.jpg"
    update_web_file(web_url,'test3')
    #print imgurl('test2')
    #print qiniu_img_info('test2')
