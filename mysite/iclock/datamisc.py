#coding=utf-8
from mysite.iclock.models import *
from django.utils.encoding import smart_str
from mysite.iclock.datautils import *
from django.shortcuts import render_to_response
from django.template import loader, Context, RequestContext, Library, Template, Context, TemplateDoesNotExist
from django.conf import settings
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

def getCopyInfo(request, ModelName):
	copyInfo = request.GET.get("key", "")
	model=models.get_model("iclock", ModelName)
	toResponse = "{"
	objs = model.objects.all()
	if objs.count():
		copyFields = objs[0].GetCopyFields()
		if model == employee:
			info = model.objects.filter(PIN=copyInfo).values(*copyFields)[0]
		elif model == iclock:
			info = model.objects.filter(SN=copyInfo).values(*copyFields)[0]
		else:
			info = model.objects.values(*copyFields)[0]	# For Exception
		for field in copyFields:
			if field == "Gender":
				toResponse += field + ":'" + ((info[field] == u'M') and _("male") or _("female")) + "',"
			else:
				f_value = info[field]
				toResponse += field + ":'" + unicode(f_value) + "',"
		toResponse = toResponse[:-1]
	toResponse += "}"
	return getJSResponse(toResponse)

def sendnew(request, ModelName):
	# 发送新的考勤记录到MS-SQL
	#from data2mssql import copyTransation
	from data2txt import copyTransation
	copyTransation()
	return getJSResponse("""'OK'""")

def DataExport(request, dataModel, qs, format):
	template=""
	format, compress=(format+'_').split("_", 1)
	formats=openExportFmt(request);
	f=formats[int(format)-1] #employee_号码姓名对照表.txt:"{{ item.PIN.PIN }}", ...
	fds =f.split("_",1)+[""]
	if fds[0]==dataModel.__name__ and fds[1]:
		fds=fds[1].split(":",1)+[""]
		if fds[0] and fds[1]: # 号码姓名对照表.txt:"{{ item.PIN.PIN }}", ...
				template=fds[1]
	fname, extname=fds[0].split(".")[-2:]
	if "_" in extname:
		extname, header=extname.split("_", 1)
	else:
		header=""
	if not template:  return render_to_response("info.html", {"title": _("Export data"), "content": _("Specified data format does not exist or do not support!")});
	if template[-1]=="\n": template=template[:-1]
	template=Template(template)
	content=[]
	if header: content=[header.decode("utf-8")]
	c=len(qs)
	for item in qs[:c>settings.MAX_EXPORT_COUNT and settings.MAX_EXPORT_COUNT or c]:
		content.append(template.render(Context({'item': item})))
	content=u"\r\n".join(content)
	response=HttpResponse()
	i=0
	if "csv" in extname:
		response["Content-Type"]="text/csv; charset="+settings.NATIVE_ENCODE
		response.write('\xEF\xBB\xBF')  
	elif "txt" in extname:
		response["Content-Type"]="text/plain; charset="+settings.NATIVE_ENCODE
		response.write('\xEF\xBB\xBF')
	else:
		response["Content-Type"]="text/plain; charset="+settings.NATIVE_ENCODE
		i=1
	response["Pragma"]="no-cache"
	response['Content-Disposition'] = u'attachment; filename='+(".".join([fname, extname]))
	response["Cache-Control"]="no-store"
	if i:
		content=content.encode('ascii')
		response["Content-Length"]=len(content);
	else:
		content=content.encode(settings.NATIVE_ENCODE)
		response["Content-Length"]=len(content)+2;
	response.write(content);
	return response

MAX_REALTIME_COUNT=100

@login_required
def newTransLog(request): #考勤记录实时监控
	result={}
	lastid=int(request.REQUEST.get("lastid","-1"));
	if lastid==-1:
		return render_to_response("logcheck.html",{},RequestContext(request, {}))
	logs=transaction.objects.filter(id__gt=lastid).order_by("-id")[:MAX_REALTIME_COUNT]
	if len(logs)>0: lastid=logs[0].id
	lines=[]
	for l in logs:
		line={}
		line['id']=l.id
		line['PIN']=l.employee().PIN
		line['EName']=l.employee().EName
		line['TTime']=l.TTime.strftime(settings.SHORT_DATETIME_FMT)
		line['State']=l.get_State_display()
		line['Verify']=l.get_Verify_display()
		line['Device']=smart_str(l.Device())
		lines.append(line.copy())
	result['msg']='OK'
	result['data']=lines
	result['lastId']=lastid
	result['ret']=len(logs)
	return getJSResponse(smart_str(simplejson.dumps(result)))

@login_required	
def newDevLog(request): #考勤记录实时监控
	device=getDevice(request.REQUEST.get('SN', ""))
	result={}
	lasttid=int(request.REQUEST.get("lasttid","-1"));
	lastdid=int(request.REQUEST.get("lastdid","-1"));
	if lasttid==-1:
		return render_to_response("dlogcheck.html",{},RequestContext(request, {}))
#	if lasttid==0:
#		logs=transaction.objects.filter(id__gt=lasttid).order_by("-id")[:1]
#	else:
	logs=transaction.objects.filter(id__gt=lasttid).order_by("-id")
	if device: logs.filter(SN=device)
	logs=logs[:MAX_REALTIME_COUNT]
	if len(logs)>0: lasttid=logs[0].id
#	if lasttid==0:
#		logs=[]
	lines=[]
	for l in logs:
		line={}
		line['id']=l.id
		line['PIN']="%s"%l.employee()
		line['TTime']=l.TTime.strftime(settings.SHORT_DATETIME_FMT)
		line['State']=l.get_State_display()
		line['Verify']=l.get_Verify_display()
		line['SC']=l.State
		line['VC']=l.Verify
		line['Device']=smart_str(l.Device())
		line['WorkCode']=l.WorkCode=="0" and " " or l.WorkCode or ""
		line['Reserved']=l.Reserved=="0" and " " or l.Reserved or ""
		line['T']=1
		line['time']=l.TTime
		lines.append(line.copy())

	logs=oplog.objects.filter(id__gt=lastdid).order_by("-id")
	if device: logs.filter(SN=device)
	if len(logs)>0: lastdid=logs[0].id
	logs=logs[:MAX_REALTIME_COUNT]
	for l in logs:
		line={}
		line['id']=l.id
		line['PIN']=l.admin or ""
		line['TTime']=l.OPTime.strftime(settings.SHORT_DATETIME_FMT)
		line['State']=u"%s"%l.ObjName() or ""
		line['Verify']=u"%s"%l.OpName()
		line['SC']=u"%s"%l.Object
		line['VC']=u"%s"%l.OP
		line['Device']=smart_str(l.Device())
		line['WorkCode']=l.Param1 or ""
		line['Reserved']=l.Param2 or ""
		line['time']=l.OPTime
		lines.append(line.copy())
	lines.sort(lambda x,y: x['time']<y['time'] and 1 or -1)
	for i in lines: i.pop("time")
	lines=lines[:MAX_REALTIME_COUNT]
	result['msg']='OK'
	result['data']=lines
	result['lasttId']=lasttid
	result['lastDId']=lastdid
	result['ret']=len(lines)
	return getJSResponse(smart_str(simplejson.dumps(result)))

@login_required	
def uploadFile(request, path): #上传文件
	if request.method=='GET':
		return render_to_response("uploadfile.html",{"title": "Only for upload file test"})
	if "EMP_PIN" not in request.REQUEST:
		return getJSResponse("result=-1; message='Not specified a target';")
	f=devicePIN(request.REQUEST["EMP_PIN"])+".jpg"
	size=saveUploadImage(request, "fileUpload", fname=getStoredFileName("photo", None, f))
	return getJSResponse("result=%s; message='%s';"%(size,getStoredFileURL("photo",None,f)))

MAX_PHOTO_WIDTH=400

def saveUploadImage(request, requestName, fname):
	import StringIO
	output = StringIO.StringIO()
	f=request.FILES[requestName]
	for chunk in f.chunks():
		output.write(chunk)
	try:
		import PIL.Image as Image
	except:
		return None
	try:
		output.seek(0)
		im = Image.open(output)
	except IOError, e:
		return getJSResponse("result=-1; message='Not a valid image file';")
	size=f.size
	if im.size[0]>MAX_PHOTO_WIDTH:
		width=MAX_PHOTO_WIDTH
		height=int(im.size[1]*MAX_PHOTO_WIDTH/im.size[0])
		im=im.resize((width, height), Image.ANTIALIAS)
	try:
		im.save(fname);
	except IOError:
		im.convert('RGB').save(fname)
	return size	

