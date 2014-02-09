#/usr/bin/env python
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

current_path = os.path.split(os.path.realpath(__file__))[0]

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

def update_web_file(web_url,name,bucket_name='tieba'):
    """
    """
    token = get_uptoken(settings.get('tieba_img_bucket'))
    extra = qiniu.io.PutExtra()
    extra.mime_type = "image/jpeg"


if __name__ == '__main__':
    pass
