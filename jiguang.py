#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import threading
import requests
import json
from utils.chars import md5_str
import time
import logging
import mdb
import tools
import settings
import traceback
import base64
from bson.objectid import ObjectId
pusher = None

class Jpush(object):
    """
    jiguang push
    """
    
    def __init__(self,app_name,app_key,master_secret):
        self.host = "http://api.jpush.cn:8800/v2/push"
        self._session = requests.Session()
        self.app_key = app_key
        self.master_secret = master_secret
        self.app_name = app_name
        self.apns_production = settings.get('jpush_apns_production')
        
    def send_notice(self,from_uid,to_uid,msg_type=1,description='yo'):
        """
        send new notice to user
        msg_type:1 yo 
        """
        to_info = mdb.yocon.user.find_one({'_id':ObjectId(to_uid)})
        print 'to_info:',to_info
        receiver_type = 3
        receiver_value = to_info['device_id']
        msg_content = json.dumps({'n_content':description,'n_extras':{'type':2,'ios':{'badge':1,'sound':'yo.m4r'},'from_uid':from_uid}})
        sendno = int(time.time())
        data = {
            "sendno":sendno,
            "msg_type":msg_type,
            "receiver_type":receiver_type,
            "receiver_value":receiver_value,
            "msg_content":msg_content,
            "platform":"ios,android",
            "verification_code":self._gen_verification_code(sendno,receiver_type,receiver_value),
        }
        return self.send_push(data)        

    def _gen_verification_code(self,sendno,receiver_type,receiver_value):
        return md5_str("%s%s%s%s"%(sendno,receiver_type,receiver_value,self.master_secret))

    def _gen_push_data(self,data):
        data['app_key'] = self.app_key
        data['msg_type'] = data['msg_type']
        data['platform'] = "android,ios" 
        data['time_to_live'] = "36000" 
        data['apns_production'] = self.apns_production
        return data
        

    def send_push(self,data):
        data = self._gen_push_data(data)
        logging.info("new jpush data:%s"%str(data))
        res = self._session.post(self.host,data=data,headers={'Content-Type':'application/x-www-form-urlencoded'})
        res_json = json.loads(res.text)
        if res_json['errcode'] == 0:
            logging.info("jpush errcode :%s"%res_json['errcode'])
        else:
            logging.error("jpush errcode :%s"%res_json['errcode'])
            logging.error("jpush errmsg :%s"%res_json['errmsg'])
        logging.info("jpush res:%s"%str(res.text))
        return res 

            
def init_pusher():
    global pusher
    pusher = Jpush('liuliu','c404b07617f6d491bf37a9fd','b0f667f1efb6d0bcaabe6391')

def push(from_uid,to_uid,msg_type=1):
    global pusher
    pusher.send_notice(from_uid,to_uid,msg_type = msg_type,description='yo')
        

if __name__ == "__main__":
    mdb.init()
    init_pusher()
    root = logging.getLogger()
    root.setLevel(settings.get('log_level'))
    push('53a2f6444056b13788e87d0a','53a2f5144056b1378805459c',1)
    
