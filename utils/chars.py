#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,sys
from hashlib import md5
from json import JSONEncoder
from bson.objectid import ObjectId
import logging
import re
#sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../.."))
#from ircd import ircServer, smallgfw

"""汉字处理

判断unicode是否是汉字，数字，英文，或者其他字符。
全角符号转半角符号。
"""

def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
        return True
    else:
        return False

def is_number(uchar):
    """判断一个unicode是否是数字"""
    if uchar >= u'\u0030' and uchar<=u'\u0039':
        return True
    else:
        return False

def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
        return True
    else:
        return False

def is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    if not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar)):
        return True
    else:
        return False

def is_num_str(uchar):
    """判断是否仅有英文和数字"""
    if is_number(uchar) or is_alphabet(uchar):
        return True
    else:
        return False

def B2Q(uchar):
    """半角转全角"""
    inside_code=ord(uchar)
    if inside_code<0x0020 or inside_code>0x7e:     #不是半角字符就返回原来的字符
        return uchar
    if inside_code==0x0020: #除了空格其他的全角半角的公式为:半角=全角-0xfee0
        inside_code=0x3000
    else:
        inside_code+=0xfee0
    return unichr(inside_code)

def Q2B(uchar):
    """全角转半角"""
    inside_code=ord(uchar)
    if inside_code==0x3000:
        inside_code=0x0020
    else:
        inside_code-=0xfee0
    if inside_code<0x0020 or inside_code>0x7e:     #转完之后不是半角字符返回原来的字符
        return uchar
    return unichr(inside_code)

def stringQ2B(ustring):
    """把字符串全角转半角"""
    return "".join([Q2B(uchar) for uchar in ustring])

def uniform(ustring):
    """格式化字符串，完成全角转半角，大写转小写的工作"""
    return stringQ2B(ustring).lower()

def string2List(ustring):
    """将ustring按照中文，字母，数字分开"""
    utmp = []
    retList=[]
    for uchar in ustring:
        if is_other(uchar):
            if len(utmp)==0:
                continue
            else:
                retList.append("".join(utmp))
                utmp=[]
        else:
            utmp.append(uchar)
    if len(utmp)!=0:
        retList.append("".join(utmp))
    return retList

def is_valid_church_name(name):
    """ 验证教会名是否合法 

    只能是数字、英文、中文
    不能是标点符号、空格等
    不能含有敏感词
    只接受unicode
    """
    if isinstance(name, str):
        name = name.decode('utf-8')

    #全角转半角，字母转小写,检测是否存在非法字符
    name = uniform(name)
    valid = True
    for uchar in name:
        if is_other(uchar):
            valid = False
            break

    #检测是否含有敏感词
    #if valid:
    #    # 如果没有gfw，从irc服务器那里初始化全部的东东
    #    if not hasattr(is_valid_church_name, 'gfw'):
    #        is_valid_church_name.gfw = ircServer.gfw
    #        if not is_valid_church_name.gfw:
    #            is_valid_church_name.gfw = smallgfw.GFW()

    #    # 若过滤结果与原来不同，则也不合法
    #    name = name.encode('utf-8')
    #    newname = is_valid_church_name.gfw.replace(name)
    #    print name, newname
    #    if newname != name:
    #        valid = False
    return valid 

def md5_str(encode_str):
    """
    md5一个字符
    """
    m = md5()
    m.update(encode_str)
    return m.hexdigest()

class mdump(JSONEncoder):
    def default(self, obj, **kwargs):
        if isinstance(obj, ObjectId):
            return str(obj)
        else:            
            return JSONEncoder.default(obj, **kwargs)

def encode_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

class InvalidInt(Exception):
    def __init__(self,num,min_num=None,max_num=None,num_range=[]):
        self.num = num
        self.min_num = min_num
        self.max_num = max_num
        self.num_range = num_range

        pass
    def __str__(self):
        return  "[is_int]invaild input %s ,min_num=%s,max_num=%s,numrange=%s"%(self.num,str(self.min_num),str(self.max_num),str(self.num_range))

class InvalidFloat(Exception):
    def __init__(self,num,min_num=None,max_num=None,num_range=[]):
        self.num = num
        self.min_num = min_num
        self.max_num = max_num
        self.num_range = num_range

        pass
    def __str__(self):
        return  "[is_float]invaild input %s ,min_num=%s,max_num=%s,num_range=%s"%(self.num,str(self.min_num),str(self.max_num),str(self.num_range))

class InvalidStr(Exception):
    def __init__(self,arg,length=None,str_range=[]):
        self.arg = arg
        self.str_range = str_range
        self.length = length

    def __str__(self):
        return  "[is_str]invaild input %s ,str_range=%s length=%s"%(self.arg,str(self.str_range),str(self.length))

def is_int(num,min_num=None,max_num=None,num_range=[]):
    """
    """
    res = int(num)
    if min_num and res <min_num:
        raise InvalidInt(num,min_num,max_num,num_range)
    if max_num and res >max_num:
        raise InvalidInt(num,min_num,max_num,num_range)
    if num_range and res not in num_range:
        raise InvalidInt(num,min_num,max_num,num_range)
    return res 
    

def is_float(num,min_num=None,max_num=None,num_range=[]):
    """
    """
    res = float(num)
    if min_num and res <min_num:
        raise InvalidFloat(num,min_num,max_num,num_range)
    if max_num and res >max_num:
        raise InvalidFloat(num,min_num,max_num,num_range)
    if num_range and res not in num_range:
        raise InvalidFloat(num,min_num,max_num,num_range)
    return res 

def not_symbol(arg,length=None,str_range=[],report=True):
    """
    """
    res = re.match(u'\w*',arg).group()
    if arg != res :
        if report:
            raise InvalidStr(arg,str_range)
        else:
            return 
    if str_range and arg not in str_range :
        if report:
            raise InvalidStr(arg,str_range)
        else:
            return 
    if length and len(res)>length :
        if report:
            raise InvalidStr(arg,length,str_range)
        else:
            return 
    
    return res
     
def is_platform(arg):
    return not_symbol(arg,str_range=['phone','sina','group'])

def is_oid(data,report=True): 
    return not_symbol(data,length=24,report=True)

nots = not_symbol

if __name__=="__main__":
    #for i in range(0x0020,0x007F):
    #    print Q2B(B2Q(unichr(i))),B2Q(unichr(i))
 
    #test uniform
    #ustring=u'中国 人名ａ高频Ａ'
    #ustring=uniform(ustring)
    #ret=string2List(ustring)
    #print ret
    #a = 'asdf啊上'.decode()
    #print 'len:',len(a)
    #print is_valid_church_name(a)
    #print is_num_str('哈as1234df'.decode('utf-8'))
    print md5_str('asdfsadaf')
