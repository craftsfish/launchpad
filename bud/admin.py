# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Supplier)
admin.site.register(Commodity)
admin.site.register(Account)
admin.site.register(Apath)
admin.site.register(Task)
admin.site.register(Transaction)
admin.site.register(Split)
admin.site.register(Organization)
admin.site.register(Opath)
