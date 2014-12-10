#!/usr/bin/env python
#coding=utf-8
from mysite.iclock.models import *
from django.conf import settings
import string,os


def defListTemp(model):
	try:
		defDataList=[f for f in model._meta.admin.list_display if f.find("_")!=0]
	except:
		defDataList=[]
	if len(defDataList)==0:
		defDataList=[f.name for f in model._meta.fields]
	defHeaderList=['"{{ cl.FieldName.%s }}"'%field for field in defDataList]
	defDataList=[(("get_"+field+"_display" in dir(model)) and  ('"{{ item.get_'+field+'_display }}"') or ('"{{ item.%s }}"'%field)) for field in defDataList]
	temp=u"""{% extends "data_list.html" %}
{% block tblHeader %}
fieldHeaders=["""+(u",".join(defHeaderList))+u"""
];
{% endblock %}
{% block rowdata %}
{% for item in latest_item_list %}
["""+(u",".join(defDataList))+u"""]{%if not forloop.last%},{%endif%}{% endfor %}
{% endblock %}
"""
	file(settings.TEMPLATE_DIRS[0]+"/"+model.__name__+'_list.html',"w+").write(temp)
	return temp

