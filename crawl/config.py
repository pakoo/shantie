#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
super_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
print 'super_dir:',super_dir
sys.path.append(super_dir)
import settings
import json
import pymongo
import random
from bson.objectid import ObjectId
from datetime import datetime
from copy import deepcopy
import requests
import mdb
import tools
from BeautifulSoup import BeautifulSoup
from smallgfw import GFW
import StringIO
import time
import traceback
import logging
from utils.ansistream import ColorizingStreamHandler
logging.StreamHandler = ColorizingStreamHandler
mdb.init()

kds = mdb.kds
tieba = mdb.tieba
connection = mdb.con
get_html = tools.get_html

baidu = mdb.baidu


root = logging.getLogger()
root.setLevel(logging.DEBUG)
