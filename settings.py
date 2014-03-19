#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.options
import random
import logging
import mdb
import time
import qiniu.conf
import server_name
from utils.ansistream import ColorizingStreamHandler
logging.StreamHandler = ColorizingStreamHandler
logging.basicConfig(level=logging.WARN,format='[%(asctime)s]%(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

tornado.options.define("env", default=server_name.name, help="environment(debug,dev,product)")

def randomize(values):
    """ this is a wrapper that returns a function which when called returns a random value"""
    def picker():
        return random.choice(values)
    return picker

options = {
    'test' : {
        'mongo_database' : {'host' : 'localhost', 'port' : 27017,'maxconnections':300,},
        'redis_para' : {'host' : 'localhost', 'port' : 6379, 'db':1},
        'tieba_img_bucket' : 'tiebaimg',
        'tieba_img_host' : 'http://tiebaimg.qiniudn.com',
        'log_level':logging.DEBUG,
        'post_flag':0,
        'server_port':8000,
        #'log_level':logging.ERROR,
    },

    'dev' : {
        'mongo_database' : {'host' : 'oucena.com', 'port' : 27017,'maxconnections':300,},
        'redis_para' : {'host' : 'oucena.com', 'port' : 6379, 'db':1},
        'tieba_img_bucket' : 'tiebaimg',
        'tieba_img_host' : 'http://tiebaimg.qiniudn.com',
        'log_level':logging.DEBUG,
        'post_flag':0,
        'server_port':8000,
        #'log_level':logging.ERROR,
    },
    
    'online' : {
        'mongo_database' : {'host' : 'localhost', 'port' : 27017,'maxconnections':300,},
        'redis_para' : {'host' : 'localhost', 'port' : 6379, 'db':1},
        'tieba_img_bucket' : 'tiebaimg',
        'tieba_img_host' : 'http://tiebaimg.qiniudn.com',
        'log_level':logging.DEBUG,
        'post_flag':0,
        'server_port':8000,
        #'log_level':logging.ERROR,
    },
}

default = {}

def get(key):
    env = tornado.options.options.env
    if env not in options:
        raise Exception("Invalid Environment (%s)" % env)
    v = options.get(env).get(key) or default.get(key)
    if callable(v):
        return v()
    return v

def init_mongo():
    """
    初始化mongodb
    """
    logging.info('mongo:%s'%str(get('mongo_database')))
    mdb.mongo_init(get('mongo_database'))


level_exp = {
            1:{'score':1,'like':1,'follow':1},
            2:{'score':21,'like':1,'follow':1},
            3:{'score':51,'like':1,'follow':1},
            4:{'score':201,'like':3,'follow':5},
            5:{'score':501,'like':3,'follow':5},
            6:{'score':1001,'like':3,'follow':5},
            7:{'score':2001,'like':5,'follow':10},
            8:{'score':4001,'like':5,'follow':10},
            9:{'score':7001,'like':5,'follow':10},
            10:{'score':12001,'like':12,'follow':24},
            11:{'score':20000,'like':12,'follow':24},
            }

init_mongo()

mdb.redis_init(get('redis_para'))

#qiniu 
qiniu.conf.ACCESS_KEY = "BeDmwwQI9g26vkU-CnNWO1OZhYsr9WBQOXAOZ7Ri"
qiniu.conf.SECRET_KEY = "rkie54djnMZNDzmesXqzW11ZXsx2XBVn39O-Qb5-"


if __name__ == '__main__':
    import tornado.ioloop
    io_loop = tornado.ioloop.IOLoop.instance()
    io_loop.add_callback(ha)
    io_loop.start()

