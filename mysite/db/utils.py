# -*- coding: utf-8 -*-

from django.db import models, connection
from django.db.models import Q
from django.template import add_to_builtins

add_to_builtins('mysite.iclock.templatetags.iclock_tags')

def getDefaultJsonDataTemplate(model, options={}):
	additionFields=[]
	exceptionFields=[]
	additionHeader={}
	try:
		exceptionFields=options.getlist('exception_fields')
	except: pass
	try:
		additionFields=options.getlist('addition_fields')
	except: pass
	if additionFields:
		fs=[]
		for f in additionFields:
			header=""
			field=f
			filter=""
			if f.find("</th>")>=0:
				header,field=f.split("</th>",1)
				header+="</th>"
				additionHeader[field]=header
			fs.append(field)
		additionFields=fs

	defDataList=[f.name for f in model._meta.fields]
	try:
		defDataListDefined=[f for f in model._meta.admin.list_display if f.find("_")!=0]
	except Exception, e:
		defDataListDefined=[]
	if defDataListDefined:
		defDataList=defDataListDefined
	if additionFields:
		defDataList=defDataList+[f for f in additionFields if f not in defDataList]
	if exceptionFields:
		defDataList=[field for field in defDataList if (field not in exceptionFields)];
	if "pk" not in defDataList:
		if model._meta.pk.name not in defDataList:
			defDataList.insert(0,model._meta.pk.name)
	defFieldList=defDataList
	defDataList=[]
	defHeaderList=[]
	for field in defFieldList:
		if ("get_"+field+"_display" in dir(model)):
			defDataList.append('"{{ item.get_'+field+'_display }}"')
		elif not field or (field[0]=="|"):
			defDataList.append('"{{ item'+field+' }}"')
		else:
			defDataList.append('"{{ item.%s }}"'%field)
		if field in additionHeader:
			defHeaderList.append('"%s"'%additionHeader[field])
		elif "|" in field: #with a filter, which must be removed
			defHeaderList.append('"{{ cl.FieldName.%s }}"'%(field.split('|')[0]))
		else:
			defHeaderList.append('"{{ cl.FieldName.%s }}"'%field.replace(".","__"))
	defFieldList=['"%s"'%f for f in defFieldList]
	temp=u"""{% autoescape off %}header:["""+ u",".join(defHeaderList)+"""],	{% endautoescape %}
field: ["""+ u",".join(defFieldList)+"""],
data:   [{% for item in latest_item_list %}
	["""+(u",".join(defDataList))+u"""]{%if not forloop.last%},{%endif%}{% endfor %}
	],
"""
	return temp
	
