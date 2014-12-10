#coding=utf-8

from mysite.iclock.models import *
from mysite.iclock.dataproc import appendDevCmd


def dispatchEmpToAll(emp):
	for dev in iclock.objects.all():
		if (dev.State<>DEV_STATUS_PAUSE) and not dev.DelTag:
			s=getEmpCmdStr(emp)
			appendDevCmd(dev, s)

def deleteEmpFromAll(pin):
	for dev in iclock.objects.all():
		appendDevCmd(dev, "DATA DELETE USERINFO PIN=%s"%pin)
