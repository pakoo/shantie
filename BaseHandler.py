#/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import logging
from bson.json_util import dumps,loads
import base64
import settings
import json
import random
from bson.objectid import ObjectId
import mdb
from utils.chars import *
import tools

class BaseHandler(tornado.web.RequestHandler):


    def sendline(self, response={}):
        """return an api response in the proper output format with status_code == 200"""
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        #self.ret['para'] = response
        if not response.get('status'):
            response['status'] = 1
        data = json.dumps(response,cls=mdump)
        logging.info('==================================================')
        logging.info('>>>>>>>response:%s'%data)
        logging.info('==================================================\n\n')
        self.finish(data)

    def senderror(self, reason='',status=0):
        """
        发送报错
        """
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        data = {'status':status,'reason':reason}
        data = json.dumps(data)
        logging.error('==================================================')
        logging.error('>>>>>>>response:%s'%data)
        logging.error('==================================================\n\n')
        self.finish(data)

    def prepare(self):
        """
        根据cookie成生玩家信息
        """
        #self.request_monitor()
        self.yres=None
        logging.info('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        #logging.info('request:%s'%str(self.request))
        llid  = self.get_cookie('llid','')
        self.api_name = self.request.uri.split('?')[0][1:]
        logging.info("useragent:%s"%self.request.headers.get('User-Agent','no user-agent'))
        #logging.info("llid:%s"%self.get_cookie('llid'))
        #logging.info("api_name:%s"%self.api_name)

        #if  self.api_name in ['','login','liyi','newpost','post/tieba','oldpost','liyi/post','tieba','tieba/post']:
        #    self.set_cookie('llid','')
        #else:
        #if True:
        #    if llid:
        #        self.uid = tools.get_user_uid_by_llid(llid)
        #        logging.info("llid to uid :%s"%(self.uid))
        #        if not self.uid:
        #            print 'isoid:',is_oid(llid,report=False)
        #            if llid and not is_oid(llid,report=False):
        #                self.redirect("/login")
        #                return 
        #            manage_info = mdb.con.manage.find_one({'_id':ObjectId(llid)})
        #        else:
        #            manage_info = None
        #        logging.info("llid to uid :%s"%(self.uid))
        #        logging.info("llid to manage_info :%s"%str(manage_info))
        #        if self.uid:
        #            #普通用户账号
        #            if self.request.uri.split('?')[0] in self.application.manager_path:
        #                #普通用户不能进管理员页面
        #                self.set_cookie('llid','')
        #                self.redirect("/login")
        #            self._id = ObjectId(self.uid)
        #            self.llid = llid
        #            self.uinfo  = tools.ruser(self.uid)
        #            self.admin=False
        #            logging.warning('##########################################')
        #            logging.warning('prepare uid:%s'%str(self.uid))
        #            logging.warning('##########################################')
        #        elif manage_info:
        #            #管理员用户
        #            self.admin=True
        #            self.status = manage_info['status'] 
        #            self.email = manage_info['email'] 
        #            self.name = manage_info['name'] 
        #            self.lluid = manage_info['lluid'] 
        #            self._id = manage_info['_id'] 
        #    else:
        #        self.redirect("/login")


class YoHandler(tornado.web.RequestHandler):

    def prepare(self):
        """
        """
        ip = self.request.headers.get('X-Forwarded-For','')
        self.ip = ip
        self.api_name = self.request.uri.split('?')[0][1:]

        yoid = self.get_cookie('yoid')
        if not yoid:
            self.finish('fuck!')
            return 
        else:
            self.yoid = yoid

        if self.api_name in ['yo_newuser'] :
            return 

        uinfo = mdb.yocon.user.find_one({'device_id':yoid})
        if  not uinfo :
            self.uid = None
            self.senderror(u'new user,registe first',status=-1)
            return 
        else:
            self.uid = str(uinfo['_id'])
            self._id = uinfo['_id']
            self.name = uinfo['name']
            self.device_id = uinfo['device_id']

    def sendline(self, response={}):
        """return an api response in the proper output format with status_code == 200"""
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        #self.ret['para'] = response
        if not response.get('status'):
            response['status'] = 1
        data = tools.dumps(response)
        logging.info('==================================================')
        logging.info('>>>>>>>response:%s'%data)
        logging.info('==================================================\n\n')
        self.finish(data)

    def senderror(self, reason='',status=0):
        """
        发送报错
        @response_status 0:请求报错
                         -1:未注册
        """
        self.set_header("Content-Type", "application/text; charset=UTF-8")
        data = {'status':status,'reason':reason}
        encode_data = tools.dumps(data)
        logging.error('==================================================')
        logging.error('>>>>>>>response:%s'%data)
        logging.error('==================================================\n\n')
        self.finish(encode_data)
    
