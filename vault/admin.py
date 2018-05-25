# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Repository)
admin.site.register(Organization)
admin.site.register(Item)
admin.site.register(Money)
admin.site.register(Supplier)
admin.site.register(Commodity)
admin.site.register(Account)
admin.site.register(Task)
admin.site.register(Transaction)
admin.site.register(Split)
admin.site.register(Jdcommodity)
admin.site.register(Jdcommoditymap)
admin.site.register(Jdorder)
