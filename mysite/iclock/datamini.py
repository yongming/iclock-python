#coding=utf-8
from mysite.iclock.models import *
from django.utils.encoding import smart_str
from mysite.utils import getJSResponse
from django.utils import simplejson

def getMiniData(request, ModelName):
	# dialog 获取数据
	miniData=request.GET.get("key", "")
	toResponse = "'"
	pk, pk_note, pk_note2, objs = (None, None, None, None)
	if miniData == "UserID":
		pk, pk_note, pk_note2 = ("id", "PIN", "EName")
		objs = employee.objects.all()
		objs=objs.order_by("PIN").values("id", "PIN", "EName")
	if miniData in ["SN","Device"]:
		pk, pk_note = ("SN", "Alias")
		objs = iclock.objects.filter(Q(DelTag__isnull=True)|Q(DelTag=0))
		objs=objs.order_by("Alias").values("SN", "Alias")
	elif miniData in ["DeptID", "depart"]:
		pk, pk_note = ("DeptID", "DeptName")
		objs = department.objects.all().values("DeptID", "DeptName")
	elif miniData in ["User", "Administrator"]:
		pk, pk_note = ("id", "username")
		objs = User.objects.all().values("id", "username")
	res={}
	if objs.count():
		for row in objs:
			res[row[pk]]=("%s"%row[pk_note])+(pk_note2 and
                (" %s"%row[pk_note2]) or "")
	toResponse = smart_str(simplejson.dumps(res))
	return getJSResponse(toResponse)
