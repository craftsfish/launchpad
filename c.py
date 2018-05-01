#!/usr/bin/env python
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import django

#setup django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "launchpad.settings")
django.setup()

#add your codes here
from vault.item import *
from vault.jd_commodity import *
#Item.Import()
Jdcommoditymap.Import()
