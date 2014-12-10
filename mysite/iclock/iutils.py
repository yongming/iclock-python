#!/usr/bin/env python
#coding=utf-8
from mysite.iclock.models import *
from mysite.utils import *
from django.db import models
from django.utils.encoding import force_unicode, smart_str
from django.contrib.auth.models import User, Permission

def userDeptList(user):
	rs_user = DeptAdmin.objects.all().filter(user=user)		
	if rs_user.count():
		if rs_user[0].dept:
			depts=getChildDept(rs_user[0].dept)
			depts.append(rs_user[0].dept)
			return depts
	return []

def userIClockList(user):
	depts=userDeptList(user)
	if depts:
		rs_SN = iclock.objects.filter(DeptID__in=depts)
		return [row.SN for row in rs_SN]
	return []

def getUserIclocks(user):
	return userIClockList(user)

def fieldVerboseName(model, fieldName):
	try:
		f = model._meta.get_field(fieldName)
		return f.verbose_name
	except:
		pass

