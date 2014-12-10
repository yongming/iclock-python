#!/usr/bin/env python
#coding=utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.cache import cache
from mysite.iclock.models import *
import string
import datetime
import time
from mysite.utils import *
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.encoding import smart_str
import sys,os
from django.db import connection as conn
from reb import *
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext 

def batchOp(request, dataModel, func):
    if request.method == 'POST':
        keys=request.POST.getlist("K")
    else: 
        keys=request.GET.getlist("K")
    info=[]
    ret=None
    for i in keys:
        d=dataModel.objects.in_bulk([i])
        ret=func(d[d.keys()[0]])
        if ("%s"%ret)==ret:
            info.append(ret)
    if len(info)>0:
        return u',\n'.join([u"%s"%f for f in info])
    return ret

dict_del_table = { # 要删除的 fk 表 记录
    str(employee) : ['fptemp'],
    str(iclock): [],
}

def delData(request, dataModel):
    if request.method == 'POST':
        keys=request.POST.getlist("K")
    else: 
        keys=request.GET.getlist("K")
    if dataModel==User:
        for i in keys:  
            if i!=request.user.id:
                d = dataModel.objects.all().filter(id=i)[0]
                if d.username != request.user.username:
                    d.delete()
    else:
        rows=dataModel.objects.filter(pk__in=keys)
        if dataModel==employee:
            for row in rows: delEmpFromDev(request.user.is_superuser, row, None)
        for row in rows: row.delete()
    return
#        return batchOp(request, dataModel, lambda d: d.delete())
    for i in keys:  # 清理 表记录
        if dataModel==User:
            d = dataModel.objects.all().filter(username=i)[0]
            d.delete()
        else:
            del_by_fk(dataModel, i)        
            d = dataModel.objects.all().filter(pk=i)[0]
            d.delete()

def delAllEmp(request, dataModel):#删除设备上所有用户信息
    if request.method == 'POST':
        keys=request.POST.getlist("K")
    else: 
        keys=request.GET.getlist("K")
    for i in keys:
        dataModel.objects.filter(SN=i).delete()

def moveEmpToDev(dev, emp, cursor=None):#转移人员数据到新设备上
    pin=emp.pin()
    device=emp.SN
    if device:
        if dev.SN==device.SN: #人员的登记设备保持不变
            return None
        appendDevCmd(device, "DATA DELETE USERINFO PIN=%s"%pin, cursor) #从原登记设备中删除
        device=emp.SN.BackupDevice()
        if device:
            appendDevCmd(device, "DATA DELETE USERINFO PIN=%s"%pin, cursor) #从备份设备中删除
    emp.SN=dev #更改人员的登记设备
    emp.save()
    return appendEmpToDev(dev, emp, cursor) #把人员的信息传送到新设备中    

def delEmpFromDev(superuser, emp, dev): #从机器中删除员工，如果没有指定机器的话，删除数据库中的员工同时在登记机和备份机中删除
    pin=emp.pin()
    if dev:
        return appendDevCmd(dev, "DATA DELETE USERINFO PIN=%s"%pin)
    if emp.SN:
        bk=emp.SN.BackupDevice()
        if bk:    
            appendDevCmd(bk, "DATA DELETE USERINFO PIN=%s"%pin)
        appendDevCmd(emp.SN, "DATA DELETE USERINFO PIN=%s"%pin)
    if superuser:
        emp.OffDuty=1
        emp.save()

def del_by_fk(dataModel, pk, app_label = "iclock"):
    table_fk = []    # 以外键方式 关联 主表 的 表
    for row in dir(dataModel.objects.all()[0]):
        r = str(row)        
        if r.endswith('_set'):
            table_fk.append(r[:-4])    
    # 去掉要删除记录的表(不把他的外键值设置为None)
    if dict_del_table.has_key(str(dataModel)):        
        for row in dict_del_table[str(dataModel)]:
            if row in table_fk:
                table_fk.remove(row)
    # 查询 外键关联的表 的pk关联记录，并设置其关联外键值为 None        
    for row_table in table_fk:    # 表        
        to_field = dataModel._meta.pk.name
        model_fk = models.get_model(app_label, row_table)
        fields = model_fk._meta.fields
        for row_field in fields:        # 字段                        
            if "ForeignKey" in str(type(row_field)):    # 外键        
                if to_field == row_field.name:
                    rs = eval("model_fk.objects.all().filter(" + to_field + "=pk)")    # 关联的记录
                    for row_rs in rs:                
                        setattr(row_rs, to_field, None)
                        row_rs.save()

def staAData(dObj, state):
    dObj.State=state
    dObj.save()

def staData(request, dataModel, state):
    batchOp(request, dataModel, lambda d: staAData(d, state))


def appendDevCmdOld(dObj, cmdStr, cmdTime=None):
    #by super 2010-08-26 协议向下兼容
    pushVersion = dObj.PushVersion or 0.0
    pushVersion = float(pushVersion)
    if pushVersion < 2.0: #旧协议命令
        cmdStr = cmdStr.replace("DATA UPDATE USERINFO","DATA USER")
        cmdStr = cmdStr.replace("DATA UPDATE FINGERTMP","DATA FP")
        cmdStr = cmdStr.replace("DATA DELETE USERINFO","DATA DEL_USER")
        cmdStr = cmdStr.replace("DATA DELETE FINGERTMP","DATA DEL_FP")
        cmdStr = cmdStr.replace("DATA UPDATE SMS","DATA SMS")

    cmd=devcmds(SN=dObj, CmdContent=cmdStr, CmdCommitTime=(cmdTime or datetime.datetime.now()))
    cmd.save()
    return cmd.id 

def appendDevCmd(dObj, cmdStr, cursor=None, cmdTime=None):
#    sql=u"insert into devcmds(sn_id, cmdcontent, cmdcommittime) values('%s','%s','%s')"%(dObj.SN, cmdStr, str(cmdTime or datetime.datetime.now())[:19])
#    print sql

#    if cursor:
#        cursor.execute(sql)
#    else:
#        cursor=conn.cursor()
#        cursor.execute(sql)
#        conn._commit()
    appendDevCmdOld(dObj, cmdStr, cmdTime)
#    deviceHasCmd(dObj)


def devNoAlarm(dObj, request):
    alarmTimeStart, alarmTimeEnd, alarmEnd=dObj.isInAlarm()
    if not alarmTimeStart: return DEV_STATUS_OK
    if datetime.datetime.now()<alarmTimeEnd: 
        return DEV_STATUS_WAIT
    else:
        appendDevCmd(dObj, "NOALARM")
        try:
            a=alarms.objects.get(SN=dObj, AlarmTime=alarmTimeEnd)
        except:
            a=alarms(SN=dObj, AlarmTime=alarmTimeStart)
        a.User=request.user
        a.NoAlarmTime=datetime.datetime.now()
        reson="NO RESON"
        try:
            reson=request.REQUEST["reson"]
        except: pass
        a.NoAlarmReson=unquote(reson)
        a.save()
        return DEV_STATUS_ALARM

def reloadDataCmd(dObj):
    dObj.OpLogStamp=0;
    dObj.LogStamp=0;
    dObj.save();
    appendDevCmd(dObj, "CHECK");

def reloadLogDataCmd(dObj):
    dObj.LogStamp=0;
    dObj.save();
    appendDevCmd(dObj, "CHECK");

def resetPwd(dev, pin, pwd, cursor):
    if pin=="0":
        appendDevCmd(dev, "RESET PWD PIN=%s\tPasswd=%s"%(1,pwd), cursor)
        appendDevCmd(dev, "RESET PWD PIN=%s\tPasswd=%s"%(2,pwd), cursor)
    else:
        appendDevCmd(dev, "RESET PWD PIN=%s\tPasswd=%s"%(pin,pwd), cursor)
    return cursor

def restoreData(dev, cursor):
    emps=employee.objects.filter(SN=dev).filter(DeptID__isnull=False)
    for emp in emps:
        appendEmpToDev(dev, emp, cursor, True)
    return cursor

def appendEmpToDev(dev, emp, cursor=None, onlyEnrollDev=False, cmdTime=None):
    bdev=None
    edev=emp.Device()
    if (not onlyEnrollDev) and edev and (edev.SN==dev.SN): 
            bdev=dev.BackupDevice()
    s=getEmpCmdStr(emp)
    #下发用户信息到设备的命令
    appendDevCmd(dev, s, cursor, cmdTime)
    print "---------------appendDevCmd ------------------"
    #by super 2010-08-16 将下发的用户信息保存到记事本
    now = datetime.datetime.now()
    filepath = os.path.abspath(os.path.dirname(sys.argv[0]))
    old_file="%s\\UserToDev%s.txt"%(tmpDir(),now.strftime("%y%m%d")[:10])    
    #write_to_file(old_file, s+'\n')
    dt = str(datetime.datetime.now())[:10]
    f = file(old_file,"w+b")
    f.write(s.encode("utf-8") + '\n')
    f.flush()
    f.close()
    if bdev: appendDevCmd(bdev, s, cursor, cmdTime)
    fps=fptemp.objects.filter(UserID=emp.id)
    for fp in fps:
        if fp.Template:
            try:
                s=u"DATA UPDATE FINGERTMP PIN=%s\tFID=%d\tSize=%s\tValid=1\tTMP=%s"%(emp.pin(), fp.FingerID, len(fp.temp()),fp.temp()) #下载 by super 2010-07-24
                appendDevCmd(dev, s, cursor, cmdTime)
                if bdev: appendDevCmd(bdev, s, cursor, cmdTime)
                #by super 2010-08-16 将下发的用户信息保存到记事本
                f = file(old_file,"w+b")
                f.write(s + '\n')
                f.flush()
                f.close()                
            except:
                errorLog()
    return cursor

def appendEmpToDevWithin(dev, emp, startTime, endTime, cursor=None):
    pin=emp.pin()
    edev=emp.Device()
    if not edev or (edev.SN!=dev.SN):
        appendEmpToDev(dev, emp, cursor, False, startTime)
        if endTime and (endTime.year>2007):
            appendDevCmd(dev, "DATA DELETE USERINFO PIN=%s"%pin, cursor, endTime)
        #delete at endTime
    return cursor

def empLeave(emp):
    dev=emp.Device()
    emp.OffDuty=1
    emp.save()
    pin=emp.pin()
    if dev:
        appendDevCmd(dev, "DATA DELETE USERINFO PIN=%s"%pin)
        bdev=dev.BackupDevice()
        if bdev:
            appendDevCmd(bdev, "DATA DELETE USERINFO PIN=%s"%pin)
            return #_("The command to delete employee %s from device %s and it's backup device %s has been sent.")%(emp, dev, bdev)
        return #_("The command to delete employee %s from device %s has been sent.")%(emp, dev)
    return #_("Employee %s has no a registration device")%emp


def copyDevEmpToDev(ddev, sdev, cursor=None):
    ret=cursor
    if ddev.SN==sdev.SN:
        return ret
    emps=employee.objects.all().filter(SN=sdev).filter(DeptID__isnull=False)
    for e in emps:
        ret=appendEmpToDev(ddev, e, cursor)
    return ret

def devCheckData(dev):
    dev.LogStamp=0
    dev.OpLogStamp=0
    dev.save()
    appendDevCmd(dev, "CHECK")

def changeEmpDept(dept, emp):
    emp.DeptID=dept
    emp.save()


def copyFromData(dataModel, obj, src, fields):
    for field in fields:        
        obj.__setattr__(field, src.__getattribute__(field))        
    obj.save()

def getFW(dev):
    ds=dev.DeviceName
#    if not ds: ds=dev.Style
    if not ds:
        ds=''
    else:
        ds=ds+"/"
    return ("file/fw/%smain.gz"%ds, "%sfw/%smain.gz"%(settings.ADDITION_FILE_ROOT,ds))

def getU(dev):
    ds=dev.DeviceName
#    if not ds: ds=dev.Style
    if not ds:
        ds=''
    else:
        ds=ds+"/"
    return ("file/fw/%semfw.cfg"%ds, "%sfw/%semfw.cfg"%(settings.ADDITION_FILE_ROOT,ds))

def getO(dev):
    ds=dev.DeviceName
#    if not ds: ds=dev.Style
    if not ds:
        ds=''
    else:
        ds=ds+"/"
    return ("file/fw/%soption2.cfg"%ds, "%sfw/%soption2.cfg"%(settings.ADDITION_FILE_ROOT,ds))


def UpdateByU(dev):
    ds=dev.FWVersion
    if not ds:
        return _(u"The Firmware version of device %(object_name)s is unknown，cannot to be upgraded!")%{'object_name':dev}
    else:
        mainVer, timeVer=ds[:8], ds[9:] #Ver 6.36 Oct 26 2007
#        if not (mainVer=="Ver 6.36" or (ds in [
#                'Ver 2.00 Oct 29 2007','Ver 2.00 Oct 30 2007','Ver 6.18 Oct 31 2007',
#                'Ver 6.18 Oct 29 2007','Ver 6.18 Oct 30 2007'])):
#            return _("device %(objdet_name)s Firmware does not support the way through the server upgrade features")%{'object_name':dev}
    url, fname=getU(dev)
    if os.path.exists(fname):
        appendDevCmd(dev, "PutFile %s\temfw.cfg"%url)
    else:
        return _(u"The firmware file '%(object_name)s' does not exist, can not upgrade firmware for %(esc_name)s!")%{'object_name':fname,'esc_name': dev}
    url, fname=getO(dev)
    if os.path.exists(fname):
        appendDevCmd(dev, "PutFile %s\toption2.cfg"%url)
    else:
        return _(u"The firmware file '%(object_name)s' does not exist, can not upgrade firmware for %(esc_name)s!")%{'object_name':fname,'esc_name': dev}


def devUpdateFirmware(dev):
    ds=dev.FWVersion
    if not ds:
        return _(u"The Firmware version of device %(object_name)s is unknown，cannot to be upgraded!")%{'object_name':dev}
    else:
        mainVer, timeVer=ds[:8], ds[9:] #Ver 6.36 Oct 26 2007
#        if not (mainVer=="Ver 6.36" or (ds in [
#                'Ver 2.00 Oct 29 2007','Ver 2.00 Oct 30 2007','Ver 6.18 Oct 31 2007',
#                'Ver 6.18 Oct 29 2007','Ver 6.18 Oct 30 2007'])):
#            return _("device %(objdet_name)s Firmware does not support the way through the server upgrade features")%{'object_name':dev}
    url, fname=getFW(dev)
    if os.path.exists(fname):
        appendDevCmd(dev, "PutFile %s\tmain.gz"%url)
    else:
        return _(u"The firmware file '%(object_name)s' does not exist, can not upgrade firmware for %(esc_name)s!")%{'object_name':fname,'esc_name': dev}

def rebootDevice(dev):
    if dev.getDynState()==DEV_STATUS_OK:
        appendDevCmd(dev, "REBOOT")
    elif dev.IPAddress:
        rebDevs([dev.IPAddress])

def clearDevData(dev):
    appendDevCmd(dev, "CLEAR DATA")        

def enrollAEmp(dev, emp):
    if not dev: dev=emp.Device()
    if not dev: return _(u"Not specified a device to enroll")
    fids=fptemp.objects.filter(UserID=emp).values_list('FingerID')
    for i in range(10):
        if (i,) not in fids:
            appendDevCmd(dev, "ENROLL_FP PIN=%s\tFID=%d\tRETRY=%d\tOVERWRITE=0"%(int(emp.PIN), i, 3))
            return
    return _('All fingerprint have enrolled')


