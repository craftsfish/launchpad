#!/usr/bin/env python
import os
import sys
import django

#setup django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "launchpad.settings")
django.setup()

#add your codes here
from console.main import *

Console.run()
