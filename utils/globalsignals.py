#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""signals的加强版，利用redis的pubsub，实现全局消息发送

主要用于向不同进程间推送指令

本模块依赖redis
"""
from gevent import monkey
monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),".."))

import logging
import settings
import redisco

from collections import defaultdict
import cPickle as pickle

class Processer():
    def __init__(self):
        self.channel = 'GLOBALSIGNALS'
        self.workers = defaultdict(set)
        self.rc = redisco.get_client()
        self.ps = self.rc.pubsub()
        self.ps.subscribe(self.channel)
        self.funcnames = set()
  
        gevent.spawn(self._listener)
    
    def _listener(self):
        for m in self.ps.listen():
            try:
                workername, message = pickle.loads(m['data'])
                try:
                    self._execute_callbacks(workername, message)
                except Exception,e:
                    logging.exception("消息处理出错")
                    logging.error("workername, %s" % workername)
                    logging.error("message, %s" % repr(message))
            except Exception,e:
                logging.exception("消息接受出错")

    def add_worker(self, workername, callback):
        from multiprocessing import current_process
        if current_process().name == 'MainProcess':
            return 
        funcname = callback.__name__
        if funcname not in self.funcnames:
            logging.debug( "增加Worker... %s:%s"%(workername,current_process()) )
            self.workers[workername].add(callback)
            self.funcnames.add(funcname)

    def _execute_callbacks(self, workername, message):
        data = message
        for w in self.workers[workername]:
            w(*data['args'],**data['kwargs'])

    def send_message(self, workername, message):
        data = pickle.dumps( (workername, message) )
        self.rc.publish(self.channel, data)

p = Processer()

def worker(workername):
    def _decorator(f):
        p.add_worker(workername, f)
        return f
    return _decorator

def signal(workername, *args, **kwargs):
    data = {'args':args,'kwargs':kwargs}
    p.send_message(workername, data)


if __name__ == '__main__':
    # 以下是信号模块的测试
    @worker('fight.finished')
    def when_fight_finished_print_signal(tip,avatar_id):
        print "fight finished"
        print "args are:", tip
        print "kwargs are:", avatar_id

    signal('fight.finished',tip='wow',avatar_id=1)
    gevent.sleep(1)
