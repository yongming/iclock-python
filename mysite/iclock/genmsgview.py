#!/usr/bin/env python
#coding=utf-8
from mysite.iclock.models import *
from django.http import QueryDict, HttpResponse, HttpResponseRedirect, HttpResponseNotModified
from django.shortcuts import render_to_response
from mysite.iclock.weatherview import genWeatherDev, checkWeatherForDev
import datetime
from django.conf import settings
from mysite.iclock.weather import getWeather
from mysite.iclock.dataproc import appendDevCmd
from django.utils.translation import ugettext as _

def genMsgForADev(device):
	checkWeatherForDev(device)

def lcdMsg(msg):
	return msg.replace(":", u"：").replace("\n","\\n").replace("\r","\\r")

def checkNewsForDev(device, type, param, now, start, mins, LastTime=None):
	for info in messages.objects.filter(StartTime__lt=now):
		if info.EndTime and info.EndTime<now: continue
		msg=info.MsgContent
		if type in [M_DEPT_NOTES, M_DEPT_SMS]: #检查并发送属于本部门的信息
			if not (not device.DeptID_id or (device.DeptID_id==info.DeptID_id)): msg=""	
		elif LastTime and info.StartTime<=LastTime:
			msg=""
		if msg:							 
			appendDevCmd(device, "SMS TAG=0x%X\tUID=1\tMIN=%s\tStartTime=%s\tMSG=%s"%(0xFD, mins, start, lcdMsg(msg)))	

def timeDiffMin(end, start):
	if not end: return 0 #UNLIMITED
	d=end-start
	return d.days*24*60+(d.seconds/60)

def genMsgForDevs():
	okDev=[]
	errorInfo=[]
	nt=datetime.datetime.now()
	now=("%s"%(nt))[:19]  #
	last=("%s"%(nt-datetime.timedelta(0,2*24*60*60)))[:19]  #两天前
#	for device in iclock.objects.exclude(DelTag=1).exclude(State=DEV_STATUS_PAUSE).exclude(LastActivity__lt=last):
	for sc in IclockMsg.objects.filter(StartTime__lt=now):#.exclude(EndTime__lt=last):
		device=sc.Device()
		try:
			start = ("%s"%sc.StartTime)[:19]
			diff = timeDiffMin(sc.EndTime, sc.StartTime)
			if not sc.EndTime or sc.EndTime>nt: ##没有结束时间，或结束时间还没有到，进行正常发送信息服务
				if sc.MsgType==M_WEATHER: # weather forecast
					checkWeatherForDev(device)
				elif sc.MsgType in (M_NEWS, M_SYS_NOTES):
					checkNewsForDev(device, sc.MsgType, sc.MsgParam, now, start, diff, sc.LastTime)
				elif (sc.MsgType in (M_DEPT_NOTES, M_DEPT_SMS)) and not sc.LastTime:
					checkNewsForDev(device, sc.MsgType, sc.MsgParam, now, start, diff)
				elif (sc.MsgType in [M_PRIV_SMS, ]) and not sc.LastTime:
					appendDevCmd(device, "SMS TAG=0x%X\tUID=%s\tMIN=%s\tStartTime=%s\tMSG=%s"%(0xFE, sc.MsgParam, diff, start, sc.MsgContent))
			elif (sc.LastTime and sc.LastTime<sc.EndTime): #已到结束时间，并且还没有处理结束工作
				#进行结束定制信息的处理
				pass
			sc.LastTime=now
			sc.save()
			okDev.append("%s"%device)
		except Exception, e:
			errorInfo.append("Error To Service messeges for %s: %s"%(device, e))
	return okDev, errorInfo	

def index(request, device):
	resp=HttpResponse(device+"\n\n", mimetype="text/plain")
	if "msg" in settings.ENABLED_MOD:
		okDev, errorInfo = genMsgForDevs()
		return render_to_response("info.html", {"title": _("Generating Messages"), "content": 
				"<pre>------------OK:\n%s\n\n-----------Fail:\n%s\n</pre>"%("\n".join(okDev), "\n".join(errorInfo))})
	else:
		return render_to_response("info.html", {"title":  _("Error"), "content": _("The server is not installed information services module!")});

	return resp
	
def get(request, device):
	if device[-1]=="/": device=device[:-1]
	resp=HttpResponse("", mimetype="text/plain")
	resp["Content-Type"]="text/plain; charset=utf-8"
	if "msg" in settings.ENABLED_MOD:
		w=getWeather(device)
		resp.write(u"\n".join(w))
		return resp
	else:
		return render_to_response("info.html", {"title":  _("Error"), "content": _("The server is not installed information services module!")});

