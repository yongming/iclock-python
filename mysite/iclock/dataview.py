#!/usr/bin/env python
#coding=utf-8
from mysite.iclock.models import *
from mysite.iclock.tools import *
from django.template import loader, Context, RequestContext, Library, Template, Context, TemplateDoesNotExist
from django.http import QueryDict, HttpResponse, HttpResponseRedirect, HttpResponseNotModified
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from exceptions import AttributeError
from django.core.cache import cache
import string,os
import datetime
import time
from mysite.utils import *
from django.core.paginator import Paginator, InvalidPage
from django.contrib.auth.decorators import login_required,permission_required
from django import forms
from mysite.iclock.dataproc import *
from django.utils.encoding import force_unicode, smart_str
from django.contrib.auth.models import User, Permission
from mysite.iclock.iutils import *
from mysite.iclock.reb	import *
from django.conf import settings
from mysite.cab import *
from mysite.iclock.devview import checkDevice 
from mysite.iclock.datv import *
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User, Group
from mysite.iclock.datautils import *
from mysite.iclock.admin_detail_view import *


PAGE_LIMIT_VAR = 'l'
TMP_VAR = 't'
def make_instance_save(instance, fields, fail_message):
    """Returns the save() method for a Form."""
    def save(self, commit=True):
        return forms.save_instance(self, instance, fields, fail_message, commit)
    return save


def form_for_model(model, instance=None, form=forms.BaseForm, fields=None, 
           formfield_callback=lambda f, **kwargs: f.formfield(**kwargs)): 
    opts = model._meta 
    field_list = []
    for f in opts.fields + opts.many_to_many: 
        if not f.editable: 
           continue 
        if fields and not f.name in fields: 
           continue 
        fst=str(type(f.formfield()))
        fstl=fst[8:-2].split('.')
        current_value = instance and f.value_from_object(instance) or None
        if 'TimeField' in fstl:
            current_value=onlyTime(current_value)
        formfield = formfield_callback(f, initial=current_value) 
        if formfield: 
            field_list.append((f.name, formfield)) 
    base_fields = SortedDict(field_list) 
    return type(opts.object_name + 'Form', (form,), 
        {'base_fields': base_fields, '_model': model, 
         'save': make_instance_save(instance or model(), fields, 'created')})

def form_for_instance(instance, form=forms.BaseForm, fields=None, 
           formfield_callback=lambda f, **kwargs: f.formfield(**kwargs)): 
    return form_for_model(instance.__class__, instance, form, fields, 
           formfield_callback)

@login_required    
def DataClear(request, ModelName):
    dataModel=GetModel(ModelName)
    if not dataModel: return NoFound404Response(request)
    if not hasPerm(request.user, dataModel, "delete"):
        return NoPermissionResponse()
    if dataModel==User:
        User.objects.exclude(id=request.user.id).delete()
    elif dataModel==iclock:
        for o in iclock.objects.all():
            cache.delete("iclock_"+o.SN)
            o.DelTag=1
            o.delete()
    else:
        try:
            dataModel.clear()
        except AttributeError, e:
            dataModel.objects.all().delete()
    adminLog(User=request.user, model=dataModel.__name__, action="Clear", object="All").save()
    return HttpResponseRedirect("../")

@login_required    
def DataDelOld(request, ModelName):
    dataModel=GetModel(ModelName)
    if not dataModel: return NoFound404Response(request)
    if not hasPerm(request.user, dataModel, "delete"):
        return NoPermissionResponse()
    try:
        delParam=dataModel.delOld()
        delOldRecords(dataModel, delParam[0], delParam[1])
    except AttributeError, e:
        errorLog(request)
    adminLog(User=request.user, model=dataModel.__name__, action="Delete out-of-date").save()
    return HttpResponseRedirect("../")

def getAvailableParentDepts(dataKey):
    child_dept_list = [] 
    pDepts=department.objects.all()
    if dataKey:
        if (dataKey=="1"):
            pDepts=[]
        else:
            rs_dept = department.objects.filter(DeptID=int(dataKey))
            if rs_dept.count():
                child_dept_list=getChildDept(rs_dept[0])
                child_dept_list.append(rs_dept[0])
                child_dept_list = [d.DeptID for d in child_dept_list]
                pDepts=pDepts.exclude(DeptID__in=child_dept_list)
    return pDepts

def ModifyFields(dataModel):
    fields = dataModel._meta.fields
    dtFields = ''        # 日期时间 字段，加日历和时间
    inputFields = ''    # 必输字段
    for field in fields:
        if "DateTimeField" in str(type(field)):
            dtFields += field.name + ','
        if field.name != 'id':
            if (not field.blank) or field.primary_key:
                inputFields += field.name + ','
    if dtFields:
        dtFields = dtFields[:-1]
    if inputFields:
        inputFields = inputFields[:-1]

    return inputFields, dtFields

def DataDetailResponse(request, dataModel, form, key=None, **kargs):
    if not kargs: kargs={}
    inputFields, dtFields=ModifyFields(dataModel)
    kargs["iclock_url_rel"]="../../.."
    request.user.iclock_url_rel=kargs["iclock_url_rel"]
    kargs["form"]=form
    kargs["title"]=(u"%s"%dataModel._meta.verbose_name).capitalize()
    kargs["dataOpt"]=dataModel._meta
    kargs["inputFields"]=inputFields
    kargs["dtFields"]=dtFields
    kargs["add"]=key==None
    if dataModel==department: # 防止把子部门更改成上级部门
        kargs["parent_dept_list"]=getAvailableParentDepts(key)
    return render_to_response([dataModel.__name__+'_edit.html','data_edit.html'],
        RequestContext(request,kargs),)    

def DataPostCheck(request, oldObj, newObj):
    if isinstance(newObj, employee):
        from mysite.iclock.datamisc import saveUploadImage
        f=devicePIN(newObj.PIN)+".jpg"
        try:
            saveUploadImage(request, "fileUpload", fname=getStoredFileName("photo", None, f))
            newObj.rmThumbnail()
        except:
            errorLog()
        if oldObj:  #修改人员数据
            old_dev=oldObj.Device()
            if int(oldObj.PIN)<>int(newObj.PIN): #changed the PIN, 需要把原来的PIN从设备中删除
                if old_dev:
                        delEmpFromDev(None, oldObj, None)
        dev=newObj.Device()
        if dev: #需要把新的人员指纹传送到设备上
            if not oldObj or (int(oldObj.PIN)<>int(newObj.PIN)): #changed the PIN, 需要把指纹等都传送一遍
                appendEmpToDev(dev, newObj)
            else:                          #只需要传送人员信息       
                cmdStr=getEmpCmdStr(newObj)
                appendDevCmd(dev, cmdStr)
                backDev=dev.BackupDevice()
                if backDev: #把新的数据传送到登记考勤机的备份机上
                    appendDevCmd(backDev, cmdStr)        


def DataNewGet(request, dataModel):    
    if dataModel==User:
        return retUserForm(request, adminForm(request), isAdd=True)
    try:
        dataForm=form_for_instance(dataModel())
    except:
        dataForm=form_for_model(dataModel)    
    return DataDetailResponse(request, dataModel, dataForm())

NON_FIELD_ERRORS = '__all__'
    
def DataNewPost(request, dataModel):    
    if dataModel==User:
        return doPostAdmin(request, dataModel, '_new_')
    dataForm=form_for_model(dataModel)
    f=dataForm(request.POST)
    if f.is_valid():
        isAdd=True

        #检查通过 DelTag 标记“删除”（隐藏）的数据
        key=(dataModel._meta.pk.name in f.cleaned_data) and f.cleaned_data[dataModel._meta.pk.name] or None
        if key:
            try:
                o=dataModel.objects.get(pk=key)
                deleted=True
                if fieldVerboseName(dataModel, "DelTag") and o.DelTag:
                    o.save()
                    return HttpResponseRedirect("../")
                f.errors[dataModel._meta.pk.name]=[_("Duplicated")]
                return DataDetailResponse(request, dataModel, f)
            except ObjectDoesNotExist:
                pass

        try:
            obj=f.save()
            key=obj.pk
        except Exception, e: #通常是不满足数据库的唯一性约束导致保存失败
            f.errors[NON_FIELD_ERRORS]=u'<ul class="errorlist"><li>%s</li></ul>'%unicode(e.message)
            return DataDetailResponse(request, dataModel, f)
        DataPostCheck(request, None, obj)

        log=adminLog(User=request.user, model=dataModel.__name__, object=u"%s"%obj)
        log.action="Create"
        log.save()
            
        popup = request.GET.get("_popup", "")
        if popup:
            the_add_object = unicode(obj)
            return HttpResponse(u'<script type="text/javascript">\nopener.dismissAddAnotherPopup(window, "%s", "%s");\n</script>' % (key, the_add_object))
            
        return HttpResponseRedirect("../")
    return DataDetailResponse(request, dataModel, f)

@login_required    
def DataNew(request, ModelName):
    dataModel=GetModel(ModelName)
    if not hasPerm(request.user, dataModel, "add"):
        return NoPermissionResponse()
    if not dataModel: return NoFound404Response(request)
    if request.method=="POST":
        return DataNewPost(request, dataModel)
    return DataNewGet(request, dataModel)

def DataChangeGet(request, dataModel, dataForm, emp):
    f=dataForm()
    if dataModel==iclock:
        backupDevice=emp.BackupDevice()
        if backupDevice:
            backupDevice=backupDevice.SN
        else:
            backupDevice=""
    return DataDetailResponse(request, dataModel, f, key=emp.pk, instance=emp)

def DataChangePost(request, dataModel, dataForm, emp):
    f=dataForm(request.POST)
    if f.is_valid():

        #检查有没有改变关键字段
        key=(dataModel._meta.pk.name in f.cleaned_data) and f.cleaned_data[dataModel._meta.pk.name] or emp.pk
        key_for_popup = key
        if key and "unicode" not in str(type(key)):
            key = unicode(key)
        if key and ('%s'%emp.pk)!=('%s'%key):
            f.errors[dataModel._meta.pk.name]=[_("Keyword \"%(object_name)s\" can not to be changed!")%{'object_name':fieldVerboseName(dataModel, dataModel._meta.pk.name)}];
            return DataDetailResponse(request, dataModel, f, key=emp.pk)
        oldEmp=None
        if dataModel==employee:
            oldEmp=employee.objByID(emp.id)
        try:
            newObj=f.save()
        except Exception, e: #通常是不满足数据库的唯一性约束导致保存失败
            f.errors[NON_FIELD_ERRORS]='<ul class="errorlist"><li>%s</li></ul>'%e.message
            return DataDetailResponse(request, dataModel, f, key=emp.pk)

        if dataModel==iclock:
            appendDevCmd(newObj, "CHECK") #命令设备读取服务器上的配置信息
            sn=request.POST["BackupDev"]
            oldsn=emp.BackupDev
            if sn and oldsn!=sn: #设置了一个新的备份设备，则把该设备登记的指纹复制到新的备份设备上
                copyDevEmpToDev(getDevice(sn), emp)
            if sn!=newObj.BackupDev:
                newObj.BackupDev = sn
                newObj.save()
        DataPostCheck(request, oldEmp or emp, newObj)

        log=adminLog(User=request.user, model=dataModel.__name__, object=u"%s"%emp)
        log.action="Modify"
        log.save()

        return HttpResponseRedirect("../")
    return DataDetailResponse(request, dataModel, f, key=emp.pk)

@login_required
def DataDetail(request, ModelName, DataKey):
    dataModel = GetModel(ModelName)
    if not hasPerm(request.user, dataModel, "change"):
        return NoPermissionResponse()
    if not dataModel: return NoFound404Response(request)

    if dataModel==User:    # 管理员 管理
        from mysite.iclock.admin_detail_view import doPostAdmin,doCreateAdmin  
        if request.method=="POST":
            return doPostAdmin(request, dataModel, DataKey)
        else:
            return doCreateAdmin(request, dataModel, DataKey)

    backupDevice=""

    emp=dataModel.objects.in_bulk([DataKey])
    if emp=={}:
        return NoFound404Response(request)
        #render_to_response("info.html", {
        #    "title": _("Edit %(object_name)s")%{"object_name":dataModel._meta.verbose_name},
        #    "content": _("Keyword \"%(object_name)s\" data do not exist!")%{'object_name':DataKey}});
    emp=emp[emp.keys()[0]]
    try:
        dataForm=form_for_instance(emp)
    except:
        dataForm=form_for_model(dataModel)

    if request.method=="POST":
        return DataChangePost(request, dataModel, dataForm, emp)
    return DataChangeGet(request, dataModel, dataForm, emp)

def getValidDevOptions():
    return ["FreeTime","COMKey"]

def getDevFromReq(request):
    key=request.REQUEST["SN"]
    try:
        ddev=getDevice(key)
        return ddev
    except:
        errorLog(request)
        return None

def getDevListFromReq(request):
    devs=[]
    keys=request.REQUEST["SN"].split(",")
    for sn in keys:
        try:
            ddev=getDevice(sn)
            devs.append(ddev)
        except:
            errorLog(request)
    return devs
                   
def strToDateDef(s, defTime=None):
    import time
    d=datetime.datetime.now()
    try:
        t=time.strptime(s, settings.STD_DATETIME_FORMAT)
        d=datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday,
            t.tm_hour, t.tm_min, t.tm_sec)
    except:
        try:#只有日期
            t=time.strptime(s, settings.STD_DATETIME_FORMAT.split(" ")[0])
            if defTime:
                d=datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, defTime[0], defTime[1], defTime[2])
            else:
                d=datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
        except Exception, e: #只有时间
            t=time.strptime(s, settings.STD_DATETIME_FORMAT.split(" ")[1])        
            d=datetime.datetime(d.year, d.month, d.day,
                t.tm_hour, t.tm_min, t.tm_sec)
    return d

def doAction(action, request, dataModel):
    cursor=conn.cursor()
    action=string.strip(action)
    ret=None
    errorInfo=""
    if action=="del":
        delData(request, dataModel)
    elif action=="pause":
        staData(request, dataModel, DEV_STATUS_PAUSE)
    elif action=="resume":
        staData(request, dataModel, DEV_STATUS_OK)
    elif action=="noalarm":
        batchOp(request, dataModel, lambda d: devNoAlarm(d, request))
    elif action=="cleardata":
        batchOp(request, dataModel, lambda d: clearDevData(d))
    elif action=="clearlog":
        batchOp(request, dataModel, lambda d: appendDevCmd(d, "CLEAR LOG"))
    elif action=="clearpic":
        batchOp(request, dataModel, lambda d: appendDevCmd(d, "CLEAR PHOTO"))
    elif action=="info":
        batchOp(request, dataModel, lambda d: appendDevCmd(d, "INFO"))
    elif action=="check":
        batchOp(request, dataModel, lambda d: devCheckData(d))
    elif action=="restart":
        batchOp(request, dataModel, lambda d: appendDevCmd(d, "RESTART"))
    elif action=="reboot":
        batchOp(request, dataModel, rebootDevice)
    elif action=="reloaddata":
        batchOp(request, dataModel, lambda d: reloadDataCmd(d))
    elif action=="reloadlogdata":
        batchOp(request, dataModel, lambda d: reloadLogDataCmd(d))
    elif action=="loaddata":
        batchOp(request, dataModel, lambda d: appendDevCmd(d, "LOG"))
    elif action=="upgradefw":
        errorInfo=batchOp(request, dataModel, lambda d: devUpdateFirmware(d))
    elif action=="upgrade_by_u-pack":
        errorInfo=batchOp(request, dataModel, lambda d: UpdateByU(d))
    elif action=="devoption":
        optName=string.strip(request.REQUEST['name'])
        optVal=string.strip(request.REQUEST['value'])
        if optName in getValidDevOptions():
            optName="SET OPTION %s=%s"%(optName, optVal)
            batchOp(request, dataModel, lambda d: appendDevCmd(d, optName))
        else:
            errorInfo=_("Device options \"%s\" Unavailable!")%optName;
    elif action=="resetPwd":
        pin=string.strip(request.REQUEST['PIN'])
        pwd=string.strip(request.REQUEST['Passwd'])
        ret=batchOp(request, dataModel, lambda dev: resetPwd(dev, pin, pwd, cursor))
    elif action=="restoreData":
        ret=batchOp(request, dataModel, lambda dev: restoreData(dev, cursor))
    elif action=="unlock":
        ret=batchOp(request, dataModel, lambda dev: appendDevCmd(dev, "AC_UNLOCK"))
    elif action=="unalarm":
        ret=batchOp(request, dataModel, lambda dev: appendDevCmd(dev, "AC_UNALARM"))
    elif action=="copy":
        src=string.strip(request.REQUEST['source'])
        src=dataModel.objects.get(pk=src)
        fields=request.REQUEST["fields"].split(";")
        batchOp(request, dataModel, lambda obj: copyFromData(dataModel, obj, src, fields))
    elif action=="copyudata": #备份登记数据到其他设备
        devs=getDevListFromReq(request)
        if not devs:
            errorInfo=_("Designated device does not exist!")
        else:
            for dev in devs:
                ret=batchOp(request, dataModel, lambda dev_: copyDevEmpToDev(dev, dev_, cursor))
    elif action=="toDev":
        devs=getDevListFromReq(request)
        if not devs:
            errorInfo=_("Designated device does not exist!")
        else:
            for dev in devs:
                ret=batchOp(request, dataModel, lambda emp: appendEmpToDev(dev, emp, cursor))
    elif action=="toDevWithin":
        devs=getDevListFromReq(request)
        if not devs:
            errorInfo=_("Designated device does not exist!")
        else:
            try:
                startTime=strToDateDef(string.strip(request.REQUEST['start']), False)
                endTime=strToDateDef(string.strip(request.REQUEST['end']), (23,59,59))
                for dev in devs:
                    ret=batchOp(request, dataModel, lambda emp: appendEmpToDevWithin(dev, emp, startTime, endTime, cursor))
            except Exception, e:
                errorInfo=e.message
    elif action=="mvToDev":
        devs=getDevListFromReq(request)
        if not devs:
            errorInfo=_("Designated device does not exist!")
        else:
            for dev in devs:
                ret=batchOp(request, dataModel, lambda emp: moveEmpToDev(dev, emp, cursor))
    elif action=="delDev":
        devs=getDevListFromReq(request)
        if not devs:
            errorInfo=_("Designated device does not exist!")
        else:
            for dev in devs:
                ret=batchOp(request, dataModel, lambda emp: appendDevCmd(dev, "DATA DELETE USERINFO PIN=%s"%emp.pin(), cursor))
    elif action=='empLeave':
        errorInfo=batchOp(request, dataModel, lambda emp: empLeave(emp))
    elif action=='enroll':
        errorInfo=batchOp(request, dataModel, lambda emp: enrollAEmp(None, emp))
    elif action=="dept":
        key=string.strip(request.GET["department"])
        try:
            dept=department.objects.get(DeptID=key)
        except:
            errorLog(request)
            errorInfo=_("%s %s does not exist!")%(department._meta.verbose_name, key)
            dept=None
        if dept:
            batchOp(request, dataModel, lambda emp: changeEmpDept(dept, emp))
    elif action=="clear_all_employee":
        delAllEmp(request, employee)
    else:
        errorInfo=_(u"Does not support this feature: \"action=%(object_name)s\"")%{'object_name':action}
    if ret==cursor:
        conn._commit()
    if errorInfo:
        return getJSResponse(u"result=-1;\nerrorInfo=\"%s\";"%errorInfo)
    else:
        return getJSResponse("result=0")
        
@login_required
def DataList(request, ModelName):
    dataModel=GetModel(ModelName)
    if not dataModel: return NoFound404Response(request)

    if (dataModel==IclockMsg) and ("msg" not in settings.ENABLED_MOD):
        return render_to_response("info.html", {"title":  _("Error"), "content": _("The server is not installed information services module!")});
    request.clear_employee=False
    if ModelName=="employee" and request.REQUEST.has_key("SN__SN__exact"):
        request.clear_employee=True
    action=request.REQUEST.get("action", "")
    if len(action)>0:
        #检查执行该动作的权限
        checkAction=action
        if action=='del':
            checkAction='delete'
        if not hasPerm(request.user, dataModel, checkAction):
            return getJSResponse("result=-2;errorInfo=\"%s\""%_("You do not have the permission!")) #NoPermissionResponse()
        adminLog(User=request.user, model=dataModel.__name__, action=action,
            object=("%s"%(request.REQUEST.get("K", "")))[:40]).save()

        return doAction(action, request, dataModel)
    request.user.iclock_url_rel='../..'
    #检查浏览该数据的权限
    if not hasPerm(request.user, dataModel, "browse"):
        return render_to_response('welcome_sys.html',RequestContext(request,{'iclock_url_rel': request.user.iclock_url_rel,}))

    
    request.model=dataModel
    qs, cl=QueryData(request, dataModel)
    
    fmt=request.REQUEST.get(EXPORT_VAR, "")
    if len(fmt)>0:
        from mysite.iclock.datamisc import DataExport
        return DataExport(request, dataModel, qs, fmt)

    #分页
    try:
        offset = int(request.GET.get(PAGE_VAR, 1))
    except:
        offset=1
    limit= int(request.GET.get(PAGE_LIMIT_VAR, settings.PAGE_LIMIT))
    state = int(request.GET.get(STATE_VAR, -1))
    if dataModel==iclock: 
        checkReboot(qs)
        if state!=-1: #由于设备状态需要计算后确定，根据设备状态过滤的页面数据不能直接从数据库获得，只能单独生成 
            return iclockPage(request, qs, offset, limit, cl, state)
    try:
        delOldCount=dataModel.delOld()[1]
    except:
        delOldCount=0
    paginator = Paginator(qs, limit)
    item_count = paginator.count
    if offset>paginator.num_pages: offset=paginator.num_pages
    if offset<1: offset=1
    pgList = paginator.page(offset)
    cc={'latest_item_list': pgList.object_list,
        'from': (offset-1)*limit+1,
        'item_count': item_count,
        'page': offset,
        'limit': limit,
        'page_count': paginator.num_pages,
        'title': (u"%s"%dataModel._meta.verbose_name).capitalize(),
        'dataOpt': dataModel._meta,
        'cl': cl,
        'delOldRecDays': delOldCount,
        'iclock_url_rel': request.user.iclock_url_rel,
        }


    tmpFile=dataModel.__name__+'_list.html'
    tmpFile=request.GET.get(TMP_VAR, tmpFile)
    try:
        if tmpFile[-3:]=='.js':
            t=loader.get_template(tmpFile)
            t_r=t.render(RequestContext(request, cc))
            return getJSResponse(smart_str(t_r))
        return render_to_response(tmpFile, cc,RequestContext(request, {}))

    except TemplateDoesNotExist:
        t=defListTemp(dataModel)
        t=Template(t)
        return HttpResponse(t.render(RequestContext(request, cc)))

def iclockPage(request, qs, offset, limit, cl, state):
    pgList=[]
    count=0
    curCount=0;
    minIndex=(offset-1)*limit
    for i in qs:
        if i.getDynState()==state:
            curCount+=1
            count=len(pgList)
            if curCount>minIndex and count<limit:
                pgList.append(i)
    pageCount=curCount/limit
    if pageCount*limit<curCount: pageCount+=1
    count=curCount

    return render_to_response('iclock_list.html', {
        'latest_item_list': pgList,
        'from': (offset-1)*limit+1,
        'page': offset,
        'limit': limit,
        'item_count': count,
        'title': (u"%s"%iclock._meta.verbose_name).capitalize(),
        'dataOpt': iclock._meta,
        'page_count': pageCount,
        'cl': cl,
        'iclock_url_rel': '..'
    },RequestContext(request, {}),)

def timeStamp(t):
    dif=t-datetime.datetime(2007,1,1)
    return "%06X%06X"%(dif.days,dif.seconds)

def stampToTime(stamp):
    dif=datetime.timedelta(string.atoi(stamp[0:3],16),string.atoi(stamp[3:],16))
    return datetime.datetime(2007,1,1)+dif

def checkReboot(iclocks):
    if not settings.REBOOT_CHECKTIME: return
    iclocks=iclocks.filter(LastActivity__lt=datetime.datetime.now()-datetime.timedelta(0,settings.REBOOT_CHECKTIME*60))
    ips=updateLastReboot(iclocks)
    rebDevs(ips)
