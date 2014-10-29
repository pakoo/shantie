#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import redis
from gevent import monkey
monkey.patch_all()
from pymongo import MongoClient
import requests

#mongodb global connection
tieba = None
baidu = None
kds = None
yy = None
#redis global connection
rcon = None
con = None
yocon = None
pusher = None
httpclient = None

def mongo_init(db_para):
    """
    初始化mongodb """
    global tieba,kds,con,baidu,yocon,yy
    mclient = MongoClient(host = db_para['host'],port=db_para['port']) 
    con = mclient
    tieba = mclient['tieba']
    baidu = mclient['baidu']
    kds = mclient['kds']
    yocon = mclient['yo']
    yy = mclient['yy']

def redis_init(redis_para):
    """
    初始化redis
    """
    global rcon
    rcon = redis.StrictRedis(host=redis_para['host'], port=redis_para['port'], db=redis_para['db'])

def init():
    import settings
    global pusher,httpclient
    mongo_init(settings.get('mongo_database'))
    redis_init(settings.get('redis_para'))
    httpclient = requests.Session()

if __name__ == '__main__':
    init()
    print rcon.get("%s_uid"%'zso6voe4ee610fezi2rq5gjq3wed8tuk')
