#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用回调来去除程序耦合

例如：

1.在任务结束的时候发送结束信号:
>>> from utils import signals
>>> signals.signal("taskcomplete", avatar_id=1, task_id=2)

2.在任务统计模块(如果有这个模块的话)收集信息并处理:
>>> from utils import signals
>>> @signals.worker("taskcomplete")
>>> def log_task(avatar_id, task_id):
...    print "用户 %s 完成了任务 %s" % (avatar_id, task_id)

则每次任务结束以后会自动输出任务完成信息

"""
import logging
from collections import defaultdict
from multiprocessing import current_process

class Processer:
    def __init__(self):
        self.workers = defaultdict(set)
        self.funcnames = set()
    
    def add_worker(self, workername, callback):
        funcname = callback.__name__
        if funcname not in self.funcnames:
            logging.debug( "增加回调Worker... %s@%s"%(workername,current_process()) )
            self.workers[workername].add(callback)
            self.funcnames.add(funcname)

    def _execute_callbacks(self, workername, message):
        if workername not in self.workers:
            logging.warning("不存在名为%s的信号接收函数!"%workername)
        else:
            try:
                data = message
                for w in self.workers[workername]:
                    w(*data['args'],**data['kwargs'])
            except Exception, e:
                logging.exception("消息处理出错")
                logging.error("workername, %s" % workername)
                logging.error("message, %s" % message)

    def send_message(self, workername, message):
        self._execute_callbacks(workername, message)

p = Processer()

def worker(workername):
    def _decorator(f):
        p.add_worker(str(workername), f)
        return f
    return _decorator

def signal(workername, *args, **kwargs):
    data = {'args':args,'kwargs':kwargs}
    p.send_message(workername, data)

if __name__ == '__main__':
    # 以下是信号模块的测试
    has_item = "has_item"

    @worker(has_item)
    def when_fight_finished_print_signal(tip,avatar_id):
        print "2tip is:", tip
        print "2avatar_id is:", avatar_id

    signal(has_item, 'wow',avatar_id=1)
