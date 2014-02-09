#encoding:utf-8
import time
def timer(func):
    """
    装饰器，用于计算程序执行时间
    """
    def wrapper(*args,**kwargs):
        start = time.time()
        result = func(*args,**kwargs)
        end = time.time()
        print "Function:'%s' used time:%s" %(func.__name__,end-start)
        print '`'*60
        print '\n\n'
        return result
    return wrapper
