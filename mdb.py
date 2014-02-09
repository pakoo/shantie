#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import redis
from gevent import monkey
monkey.patch_all()
from pymongo import MongoClient

#mongodb global connection
tieba = None
kds = None
#redis global connection
rcon = None

def mongo_init(db_para):
    """
    初始化mongodb """
    global tieba,kds
    mclient = MongoClient(host = db_para['host'],port=db_para['port']) 
    tieba = mclient['tieba']
    kds = mclient['kds']

def redis_init(redis_para):
    """
    初始化redis
    """
    global rcon
    rcon = redis.StrictRedis(host=redis_para['host'], port=redis_para['port'], db=redis_para['db'])

def init():
    import settings
    mongo_init(settings.get('mongo_database'))
    redis_init(settings.get('redis_para'))

if __name__ == '__main__':
    init()
    print rcon.get("%s_uid"%'zso6voe4ee610fezi2rq5gjq3wed8tuk')
