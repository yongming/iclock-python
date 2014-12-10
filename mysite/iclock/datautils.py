#coding=utf-8
from mysite.iclock.models import *
from django.utils.encoding import smart_str
import operator
from mysite.iclock.filterspecs import FilterSpec
from mysite.iclock.iutils import *
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.template import loader, Context, RequestContext
from django.conf import settings

ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'

SEARCH_VAR = 'q'
IS_POPUP_VAR = 'pop'
ERROR_FLAG = 'e'
STATE_VAR = 's'
EXPORT_VAR = 'f'
PAGE_LIMIT_VAR = 'l'
TMP_VAR = 't'

def createNewOrdUrl(ordUrl, fieldName, remove):
	ordFields=(ordUrl or "").split(',')
	if "" in ordFields: ordFields.remove("")
	desc=False
	sorted=False
	if fieldName in ordFields:
		sorted=True
		if remove:
			ordFields.remove(fieldName)
		else:
			index=ordFields.index(fieldName)
			ordFields[index]="-"+fieldName
	elif ("-"+fieldName) in ordFields:
		desc=True
		sorted=True
		if remove:
			ordFields.remove("-"+fieldName)
		else:
			index=ordFields.index("-"+fieldName)
			ordFields[index]=fieldName
	elif not remove:
		desc=True
		ordFields.append(fieldName)
	else:
		return ""
	return ",".join(ordFields), sorted, desc

class FieldNameMulti(object): #支持多字段排序
	def __init__(self, cl, orderUrl=True):
		self.cl=cl
		self.desc=1
		self.orderUrl=orderUrl

	def __getitem__(self, fieldName):
		for f in self.cl.model._meta.fields:
			if f.name==fieldName:
				orderStr, sorted, desc=createNewOrdUrl(self.cl.orderStr, fieldName, False)
				orderStr=self.cl.get_query_string({ORDER_VAR:orderStr},[ORDER_VAR]).replace("'","\\'").replace('"','\\"')
				if self.orderUrl:
					if sorted:
						if desc:
							ret="<th class='sorted descending'>%s<div class='order_hd'><a href='"+orderStr+"'>^</a>"
						else:
							ret="<th class='sorted ascending'>%s<div class='order_hd'><a href='"+orderStr+"'>v</a>"
						removeOrderStr, sorted, desc=createNewOrdUrl(self.cl.orderStr, fieldName, True)
						if removeOrderStr:
							removeOrderStr=self.cl.get_query_string({ORDER_VAR:removeOrderStr},[ORDER_VAR]).replace("'","\\'").replace('"','\\"')
						else:
							removeOrderStr=self.cl.get_query_string({},[ORDER_VAR])
						ret+="<a href='"+removeOrderStr+"'>X</a></div></th>"
					else:
						ret="<th>%s<div class='order_hd'><a href='"+orderStr+"'>^</a></div></th>"
					ret=ret%((u"%s"%f.verbose_name).capitalize())
				else:
					ret="<th abbr='"+fieldName+"'>%s</th>"%(u"%s"%f.verbose_name).capitalize()
				return ret
		return ""

class FieldName(object):
	def __init__(self, cl, orderUrl=True):
		self.cl=cl
		self.desc=1
		self.orderUrl=orderUrl
		if cl.orderStr:
			if cl.orderStr[0:1]=="-":
				self.desc=0
				self.orderField=cl.orderStr[1:]
			else:
				self.orderField=cl.orderStr
		else:
			self.orderField=""
	def __getitem__(self, fieldName):
		for f in self.cl.model._meta.fields:
			if f.name==fieldName:
				orderStr=fieldName
				if self.orderUrl:
					if fieldName==self.orderField:
						if self.desc:
							orderStr="-%s"%fieldName
							ret="<th class='sorted descending'><a href='%s'>%s</a></th>"
						else:
							ret="<th class='sorted ascending'><a href='%s'>%s</a></th>"
					else:
						ret="<th><a href='%s'>%s</a></th>"
					orderStr=self.cl.get_query_string({ORDER_VAR:orderStr},[ORDER_VAR])
					orderStr=string.join(orderStr.split('"'),'\\"')
					orderStr=string.join(orderStr.split("'"),"\\'")
					ret=ret%(orderStr, (u"%s"%f.verbose_name).capitalize())
				else:
					ret="<th abbr='"+fieldName+"'>%s</th>"%(u"%s"%f.verbose_name).capitalize()
				return ret
		return ""


def openExportFmt(request):
	try:
		formats=file(settings.TEMPLATE_DIRS[0]+"/export_formats_"+request.LANGUAGE_CODE+".txt","r").readlines();
	except:
		formats=file(settings.TEMPLATE_DIRS[0]+"/export_formats.txt","r").readlines();
	return formats

def xlist2str(list1 = []):
	str1 = ""
	if list1:
		for li in list1:
			str1 += li + ","
	if str1:
		str1 = str1[:-1]
	return str1

def getVerboseName(model, name):
	for field in model._meta.fields:
		if field.name == name:
			return u"%s"%field.verbose_name
	return ""
			   
class ChangeList(object):
	def __init__(self, request, model):
		self.model = model
		self.opts = model._meta
		self.params = dict(request.GET.items())
		self.filter_specs, self.has_filters = get_filters(self.opts, request, self.params, model)
		self.request=request
		self.orderStr=""
		self.lng=request.LANGUAGE_CODE
		if ORDER_VAR in self.params:
			self.orderStr=self.params[smart_str(ORDER_VAR)]
		elif model==iclock:
			self.orderStr="Alias"
		elif model._meta.pk.name=="id":
			self.orderStr="-id"

		self.FieldName=FieldName(self, request.GET.get(ORDER_TYPE_VAR, '0')=='1')

		searchHint=[]
		if self.opts.admin:
			for f in self.opts.fields:
				try:
					if f.name in self.opts.admin.search_fields:
						searchHint.append((u"%s"%f.verbose_name).capitalize())
				except: pass
		if len(searchHint)>0:
			self.searchHint=string.join(searchHint, ",")
		else:
			self.searchHint=None

	def GetCopyFields(self):
		self._initCopyFields(self, self.model)

	def _initCopyFields(self, model):
		objs = model.objects.all()
		if objs.count():
			obj = objs[0]
			if model == employee or model == iclock:
				return xlist2str([field + ":" + u"%s"%getVerboseName(model, field)for field in obj.GetCopyFields()])
			else:
				return ""

	def get_query_string(self, new_params=None, remove=None):
		if new_params is None: new_params = {}
		if remove is None: remove = []
		p = self.params.copy()
		for r in remove:
			for k in p.keys():
				if k.startswith(r):
					del p[k]
		for k, v in new_params.items():
			if k in p and v is None:
				del p[k]
			elif v is not None:
				p[k] = v
		return '?' + '&amp;'.join([u'%s=%s' % (k, v) for k, v in p.items()]).replace(' ', '%20')

	def getDataExportsFormats(self):
		fl=[]
		formats=openExportFmt(self.request)
		index=0
		for f in formats:
			fds =(f+"_").split("_",1)
			index+=1
			if fds[0]==self.model.__name__ and fds[1]:
				fds=(fds[1]+":").split(":")
				if fds[0] and fds[1]:
					fl.append((index, unicode(fds[0].split('.')[0].decode("utf-8")),))
		return fl

def construct_search(field_name):
		if field_name.startswith('^'):
			return "%s__istartswith" % field_name[1:]
		elif field_name.startswith('='):
			return "%s__iexact" % field_name[1:]
		elif field_name.startswith('@'):
			return "%s__search" % field_name[1:]
		else:
			return "%s__icontains" % field_name

def get_filters(opts, request, params, dataModel):
	filter_specs = []
	try:
		if opts.admin and opts.admin.list_filter and not opts.one_to_one_field:
			filter_fields = [opts.get_field(field_name) \
				for field_name in opts.admin.list_filter]
			for f in filter_fields:
				spec = FilterSpec.create(f, request, params, dataModel)
				if spec and spec.has_output():
					filter_specs.append(spec)
	except Exception, e:
		pass
	return filter_specs, bool(filter_specs)

def QueryData(request, dataModel):
	opts = dataModel._meta
	params = dict(request.GET.items())
	if not opts.admin: 
		try:
			opts.admin=dataModel.Admin
		except: pass

	#查询
	if fieldVerboseName(dataModel, "DelTag"):
		qs=dataModel.objects.filter(Q(DelTag__isnull=True)|Q(DelTag=0))
	else:
		qs=dataModel.objects.all()
	search=request.GET.get(SEARCH_VAR,"")
	search=unquote(search);
	if request.GET.has_key(SEARCH_VAR) and opts.admin.search_fields:
		for bit in search.split():
			or_queries = [models.Q(**{construct_search(field_name): bit}) for field_name in opts.admin.search_fields]
			other_qs = dataModel.objects.all()
			try:
				other_qs.dup_select_related(qs)
			except:			
				if qs._select_related:
					other_qs = other_qs.select_related()
			other_qs = other_qs.filter(reduce(operator.or_, or_queries))
			qs = qs & other_qs

	#过滤
	lookup_params = params.copy() # a dictionary of the query string
	for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, PAGE_VAR, STATE_VAR, EXPORT_VAR,PAGE_LIMIT_VAR,TMP_VAR):
		if i in lookup_params:
			del lookup_params[i]
	for key, value in lookup_params.items():
		if not isinstance(key, str):
		# 'key' will be used as a keyword argument later, so Python
		# requires it to be a string.
			del lookup_params[key]
			k=smart_str(key)
			lookup_params[k] = value
		else:
			k=key
		if (k.find("__in")>0) or (k.find("__exact")>0 and value.find(',')>0):
			del lookup_params[key]
			lookup_params[k.replace("__exact","__in")]=value.split(",")
	# Apply lookup parameters from the query string.
	if lookup_params:
		qs = qs.filter(**lookup_params)
	# 查询考勤记录的权限限制
	if not request.user.is_superuser:
		if request.user.username=='employee':
				qs = qs.filter(UserID=request.employee)
		elif 'UserID' in dir(dataModel):
			dept_list=userDeptList(request.user)
			userList=employee.objects.filter(DeptID__in=dept_list)
			qs = qs.filter(UserID__in=userList)
		elif 'DeptID' in dir(dataModel):
			dept_list=userDeptList(request.user)
			qs = qs.filter(DeptID__in=dept_list)
		elif 'SN' in dir(dataModel):
			sn_list=userIClockList(request.user)
			qs = qs.filter(SN__in=sn_list)
		elif 'Children' in dir(dataModel):
			dept_list=userDeptList(request.user)
			dd=[]
			for i in dept_list:
				dd.append(int(i.DeptID))
			qs = qs.filter(DeptID__in=dd)
		

	#排序
	cl=ChangeList(request, dataModel)
	if cl.orderStr:
		ot=cl.orderStr.split(",")
		qs=qs.order_by(*ot)
				
	return qs, cl

def NoPermissionResponse(title=''):
	return render_to_response("info.html", {"title": title, "content": _("You do not have the permission!")});	

def GetModel(ModelName):
	dataModel=models.get_model("iclock",ModelName)
	if not dataModel:
		dataModel=models.get_model("auth",ModelName)
	return dataModel

def hasPerm(user, model, operation):
	modelName=model.__name__.lower()
	perm='%s.%s_%s'%(model._meta.app_label, operation,modelName)
	return user.has_perm(perm)

def NoFound404Response(request):
	return render_to_response("404.html",{"url":request.path},RequestContext(request, {}),);
