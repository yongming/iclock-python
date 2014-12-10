#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models, connection
from django.db.models import Q
from django.contrib.auth.models import User, Permission, Group
import datetime
import os
import string
from django.contrib import auth
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from mysite.utils import *
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.forms.models import ModelChoiceIterator
from redis.server import queqe_server

AUDIT_STATES=(
    (0,_('Apply')),
    (1,_('Auditing')),
    (2,_('Accepted')),
    (3,_('Refused')),
    (4,_('Paused')),
    (5,_('Re-Apply')),
    (6,_('Again')),
    (7,_('Cancel_leave'))
)
DEPT_NAME=_("department")
DEPT_NAME_2=_("department name")
DEPT_NAME_ID=_("department number")

def getDefaultDept():
    """ 获取默认部门；没，则创建
        """
    try:
        dept = department.objects.get(DeptID=1)
    except:
        try:
            dept = department(DeptID=1, DeptName="Default Dept", parent=0)
            dept.save()
        except:
            dept = department.objects.all()[0]
    return dept

class NestedDeptException(Exception): pass

class department(models.Model):
    DeptID = models.IntegerField(DEPT_NAME_ID,primary_key=True)
    DeptName = models.CharField(DEPT_NAME_2,max_length=20)
    parent = models.IntegerField( db_column="supdeptid",verbose_name=_('parent'), null=False, blank=True, default=1)
    def Parent(self):
        if self.parent:
            return self.objByID(self.parent)
        return None
    @staticmethod    
    def clear():
        deptid=getDefaultDept().DeptID
        for dept in department.objects.exclude(DeptID=deptid): 
            dept.delete()
    def AllParents(self):
        ps=[]
        d=self
        for i in range(100):
            try:
                d=self.objByID(d.parent)
                ps.append(d)
                if d==self: break;
            except:
                break
        return ps
    def Children(self):
        return department.objects.filter(parent=self.DeptID)
    def AllChildren(self, start=[]):
        for d in self.Children():
            if d not in start:
                start.append(d)
                d.AllChildren(start)
    @staticmethod
    def objByID(id):
        if id==None: return None
        d=cache.get("%s_iclock_dept_%s"%(settings.UNIT,id))
        if d: return d
        d=department.objects.get(DeptID=id)
        if d:
            cache.set("%s_iclock_dept_%s"%(settings.UNIT,id),d)
        return d
    def __unicode__(self):
        try:
            return u"%d %s"%(self.DeptID, self.DeptName.decode("utf-8"))
        except:
            return u"%d %s"%(self.DeptID, unicode(self.DeptName))
    def save(self):
        if (department.objects.all().count()==0) or ((not self.parent) or department.objects.filter(DeptID=self.parent).count()>0):
            if (not self.parent) or (self.DeptID==1): self.parent=0
            if self in self.AllParents():
                raise NestedDeptException(_('Nested department parent'))
            cache.set("%s_iclock_dept_%s"%(settings.UNIT,self.DeptID),self)
            models.Model.save(self)
        else:
            raise Exception("Parent is not exist.")
    def delete(self):
        deptid=getDefaultDept().DeptID
        if self.DeptID==deptid: return
        try:
            cache.delete("%s_iclock_dept_%s"%(settings.UNIT,self.DeptID))
        except: pass
        for dev in iclock.objects.filter(DeptID=self):
            dev.DeptID=None
            dev.save()
        super(department, self).delete()
    class Admin:
        search_fields = ['DeptName']
    class Meta:
        db_table = 'departments'
        verbose_name=DEPT_NAME
        verbose_name_plural=verbose_name

# 获得部门的下级所有部门
def getChildDept(dept):
    child_list=[]
    dept.AllChildren(child_list)
    return child_list


BOOLEANS=((0,_("No")),(1,_("Yes")),)

DEV_STATUS_OK=1
DEV_STATUS_TRANS=2
DEV_STATUS_OFFLINE=3
DEV_STATUS_PAUSE=0

nocmd_device_cname="%s_nocmd_device"%settings.UNIT

def deviceCmd(device):
    nocmd_device=[]
    if nocmd_device_cname in cache:
        nocmd_device=cache.get(nocmd_device_cname)
    if nocmd_device and (device.SN in nocmd_device):
        cmds=[]
    else:
        cmds=devcmds.objects.filter(SN=device,CmdOverTime__isnull=True).order_by('id')[:1000]
        if len(cmds)==0:
            if not nocmd_device: nocmd_device=[]
            nocmd_device.append(device.SN)
            cache.set(nocmd_device_cname, nocmd_device)
        nowCmds=[]
        now=str(datetime.datetime.now())
        for cmd in cmds:
            if str(cmd.CmdCommitTime)<=now: nowCmds.append(cmd)
        return nowCmds
    return cmds

import socket
sNotify = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def deviceHasCmd(device):
    try:
        nocmd_device=cache.get(nocmd_device_cname)
        if nocmd_device:
            nocmd_device.remove(device.SN)
            cache.set(nocmd_device_cname, nocmd_device)
    except: pass
    try:
        ip=device.IPAddress
        if ip: sNotify.sendto("R-CMD", (ip, 4374))
    except:
        errorLog()
        pass

def getValueFrom(data, key):
    d={}
    for v in data.split("\n"):
        if v:
            if v[-1] in ['\r','\n']: v=v[:-1]
        nv=v.split("=")
        if len(nv)>1:
            if key==nv[0]:
                return "=".join(nv[1:])
    return ""

def setValueDic(data):
    d={}
    for line in data.split("\n"):
        if line:
            v=line.split("\r")[0]
        else:
            v=line
        nv=v.split("=", 1)
        if len(nv)>1:
            try:
                v=str(nv[1])
                d[nv[0]]=v
            except:
                pass
    return d

def setValueFor(data, key, value):
    d={}
    for line in data.split("\n"):
        if line:
            v=line.split("\r")[0]
        else:
            v=line
        nv=v.split("=", 1)
        if len(nv)>1:
            try:
                v=str(nv[1])
                d[nv[0]]=v
            except:
                pass
    if key:
        d[key]=value
    return "\n".join(["%s=%s"%(k, d[k]) for k in d.keys()])

def mergeValues(data1, data2):
    return setValueFor(data1+"\n"+data2, "","")

last_reboot_cname="%s_lastReboot"%settings.UNIT    

def updateLastReboot(iclocks):
    lastReboot=cache.get(last_reboot_cname)
    d=datetime.datetime.now()
    rebInterval=(REBOOT_CHECKTIME>0 and REBOOT_CHECKTIME or 10)
    ips=[]
    if not lastReboot: lastReboot={}
    for i in iclocks:
        ip=i.IPAddress()
        if ip:
            if ip in lastReboot:
                if d-lastReboot[ip]>datetime.timedelta(0,rebInterval*60):
                    ips.append(ip)
                    lastReboot[ip]=d
            else:
                ips.append(ip)
                lastReboot[ip]=d
    if ips: cache.set(last_reboot_cname, lastReboot, rebInterval*60)
    return ips

def removeLastReboot(ip):
    lastReboot=cache.get(last_reboot_cname)
    if not lastReboot: return
    if ip in lastReboot:
        lastReboot.pop(ip)
        cache.set(last_reboot_cname, lastReboot)
def checkTime(t):
    if str(type(t))=="<type 'datetime.datetime'>":
        return datetime.datetime(t.year,t.month,t.day,t.hour,t.minute,t.second)
    elif str(type(t))=="<type 'datetime.time'>":
        return datetime.datetime(1899,12,30,t.hour,t.minute,t.second)
    elif str(type(t))=="<type 'datetime.date'>":
        return datetime.datetime(t.year,t.month,t.day,0,0,0)


TIMEZONE_CHOICES=(
    (-750,'Etc/GMT-12:30'),
    (-12,'Etc/GMT-12'),
    (-690,'Etc/GMT-11:30'),
    (-11,'Etc/GMT-11'),
    (-630,'Etc/GMT-10:30'),
    (-10,'Etc/GMT-10'),
    (-570,'Etc/GMT-9:30'),
    (-9,'Etc/GMT-9'),
    (-510,'Etc/GMT-8:30'),
    (-8,'Etc/GMT-8'),
    (-450,'Etc/GMT-7:30'),
    (-7,'Etc/GMT-7'),
    (-390,'Etc/GMT-6:30'),    
    (-6,'Etc/GMT-6'),
    (-330,'Etc/GMT-5:30'),
    (-5,'Etc/GMT-5'),
    (-270,'Etc/GMT-4:30'),
    (-4,'Etc/GMT-4'),
    (-210,'Etc/GMT-3:30'),
    (-3,'Etc/GMT-3'),
    (-150,'Etc/GMT-2:30'),
    (-2,'Etc/GMT-2'),
    (-90,'Etc/GMT-1:30'),
    (-1,'Etc/GMT-1'),
    (-30,'Etc/GMT-0:30'),
    (0,'Etc/GMT'),
    (30,'Etc/GMT+0:30'),
    (1,'Etc/GMT+1'),
    (90,'Etc/GMT+1:30'),
    (2,'Etc/GMT+2'),
    (150,'Etc/GMT+2:30'),
    (3,'Etc/GMT+3'),
    (210,'Etc/GMT+3:30'),
    (4,'Etc/GMT+4'),
    (270,'Etc/GMT+4:30'),
    (5,'Etc/GMT+5'),
    (330,'Etc/GMT+5:30'),
    (6,'Etc/GMT+6'),
    (390,'Etc/GMT+6:30'),    
    (7,'Etc/GMT+7'),
    (450,'Etc/GMT+7:30'),
    (8,'Etc/GMT+8'),
    (510,'Etc/GMT+8:30'),
    (9,'Etc/GMT+9'),
    (570,'Etc/GMT+9:30'),
    (10,'Etc/GMT+10'),
    (630,'Etc/GMT+10:30'),
    (11,'Etc/GMT+11'),
    (690,'Etc/GMT+11:30'),
    (12,'Etc/GMT+12'),
    (750,'Etc/GMT+12:30'),
    (13,'Etc/GMT+13'),
    (810,'Etc/GMT+13:30'),
)


class iclock(models.Model):
    SN = models.CharField(_('serial number'), max_length=20, primary_key=True, help_text=_('Should be set with the device, on the device, access management menu "Sys Info" / "Dev Info" / "Serial Num" could be found'))
    State = models.IntegerField(u'状态',default=1, editable=False)
    LastActivity = models.DateTimeField(_('last activity'),null=True, blank=True)
    TransTimes = models.CharField(_('transfer time'),max_length=50, null=True, blank=True, default="00:00;14:05", help_text=_('Setting device for a moment from the plane started to send checks to the new data server. Hh: mm (hours: minutes) format, with a number of time between the semicolon (;) separately'))
    TransInterval = models.IntegerField(_('interval'),default=1, help_text=_('Device set for each interval to check how many minutes to send new data server'))
    LogStamp = models.CharField(_('trans record stamp'),max_length=20, null=True, blank=True, help_text=_('Logo for the latest device to the server send the transactions timestamps'))
    OpLogStamp = models.CharField(_('trans OP stamp'),max_length=20, null=True, blank=True, help_text=_('Marking device for the server to the employee data transfer as timestamps'))
    PhotoStamp = models.CharField(_('trans photo stamp'),max_length=20, null=True, blank=True, help_text=_('Marking device for the server to the picture transfer as timestamps'))
    Alias = models.CharField(_('Device Alias name'),max_length=20, help_text=_('Device of a name')) #by super 2010-08-11 设备别名
    DeptID = models.ForeignKey("department", db_column="DeptID", verbose_name=DEPT_NAME, default=1,editable=True, null=True)
    #UpdateDB = models.CharField(_('update flag'),max_length=10, default="1111100000", blank=True, editable=True, help_text=_('To identify what kind of data should be transfered to the server'))
    UpdateDB = models.CharField(_('update flag'),max_length=200, default="TransData AttLog\tOpLog\tEnrollUser\tChgUser\tChgFP\tAttPhoto\tEnrollFP", blank=True, editable=True, help_text=_('To identify what kind of data should be transfered to the server')) #by super 2010-07-22
    Style = models.CharField(_('style'),max_length=20, null=True, blank=True, default="F7", editable=False)
#    Info = models.TextField(_('info'), max_length=8*1024, null=True, blank=True)
    FWVersion = models.CharField(_('FW Version'),max_length=30, null=True, blank=True,editable=False)
    FPCount = models.IntegerField(_('FP Count'), null=True, blank=True,editable=False)
    TransactionCount = models.IntegerField(_('Transaction Count'), null=True, blank=True,editable=False)
    UserCount = models.IntegerField(_('User Count'), null=True, blank=True,editable=False)
    MainTime = models.CharField(_('MainTime'),max_length=20, null=True, blank=True,editable=False)
    MaxFingerCount = models.IntegerField(_('MaxFingerCount'), null=True, blank=True,editable=False)
    MaxAttLogCount = models.IntegerField(_('MaxAttLogCount'), null=True, blank=True,editable=False)
    DeviceName = models.CharField(_('Device Name'),max_length=30, null=True, blank=True,editable=False)
    AlgVer = models.CharField(_('AlgVer'),max_length=30, null=True, blank=True,editable=False)
    FlashSize = models.CharField(_('FlashSize'),max_length=10, null=True, blank=True,editable=False)
    FreeFlashSize = models.CharField(_('FreeFlashSize'),max_length=10, null=True, blank=True,editable=False)
    Language = models.CharField(_('Language'),max_length=30, null=True, blank=True,editable=False)
    VOLUME = models.CharField(_('VOLUME'),max_length=10, null=True, blank=True,editable=False)
    DtFmt = models.CharField(_('DtFmt'),max_length=10, null=True, blank=True,editable=False)
    IPAddress = models.CharField(_('IPAddress'),max_length=20, null=True, blank=True,editable=False)
    IsTFT = models.CharField(_('IsTFT'),max_length=5, null=True, blank=True,editable=False)
    Platform = models.CharField(_('Platform'),max_length=20, null=True, blank=True,editable=False)
    Brightness = models.CharField(_('Brightness'),max_length=5, null=True, blank=True,editable=False)
    BackupDev = models.CharField(_('Auto backup data to'),max_length=30, null=True, blank=True)
    OEMVendor = models.CharField(_('OEMVendor'),max_length=30, null=True, blank=True,editable=False)
    City = models.CharField(_('city'),max_length=50, null=True, blank=True, help_text=_('City of the location'))
    LockFunOn = models.SmallIntegerField(db_column='AccFun', default=0, blank=True, editable=False, help_text=_('Access Function'))
    TZAdj = models.SmallIntegerField(_('Timezone'), default=8, blank=False, editable=True, help_text=_('Timezone of the location'), choices=TIMEZONE_CHOICES)
    DelTag = models.SmallIntegerField(max_length=1, default=0, editable=False, null=False, blank=True)
    FPVersion = models.CharField(max_length=10, editable=False, null=True, blank=True) #by super 2010-08-26 指纹算法
    PushVersion = models.CharField(max_length=10, default=0.0, editable=False, null=True, blank=True) #by super 2010-08-26 协议版本,>=2.0为新协议

    def GetCopyFields(self):
        return ["TransTimes", "TransInterval"]

    def getInfo(self, info):
        if not self.Info: return ""
        return getValueFrom(self.Info, info)

    def IsTft(self):
        ret=self.IsTFT
        if ret and ret=="1": return True
        ret=self.Platform
        if ret and ret.find("_TFT")>0: return True
        ret=self.Brightness
        if ret and ret>"0": return True
        return False
    def BackupDevice(self):
        sn=self.BackupDev
        if not sn: return None
        try:
            return getDevice(sn)
        except:
            pass
    def getDynState(self):
        try:
            if self.State==DEV_STATUS_PAUSE: return DEV_STATUS_PAUSE
            aObj=cache.get("iclock_"+self.SN)
            if aObj and aObj.LastActivity>self.LastActivity:
                self.LastActivity=aObj.LastActivity
            if not self.LastActivity: return DEV_STATUS_OFFLINE
            d=datetime.datetime.now()-self.LastActivity
            if d>datetime.timedelta(0,90):#update by Louis 2011-12-26,device statu,
                return DEV_STATUS_OFFLINE

#如果有命令日志记录，返回
            if len(deviceCmd(self))>0:#if devcmds.objects.filter(SN=self,CmdOverTime__isnull=True).count()>0:
                return DEV_STATUS_TRANS
            return DEV_STATUS_OK
        except:
            errorLog()
    def getImgUrl(self):
        if self.DeviceName:
            imgUrl=settings.MEDIA_ROOT+'img/device/'+self.DeviceName+'.png'
            if os.path.exists(imgUrl):
                return settings.MEDIA_URL+'/img/device/'+self.DeviceName+'.png'
        return settings.MEDIA_URL+'/img/device/noImg.png'
    def getThumbnailUrl(self):
        return self.getImgUrl()
    def save(self, raw=None):
        if self.DelTag: self.DelTag=0
        try:
            cache.set("iclock_"+self.SN, self)
        except:
            raise Exception(_(u"Invalid %s")%_(u'serial number'))
        return models.Model.save(self)
    def clear(self):
        for o in self.model.objects.all().filter(DelTag__isnull=True):
            cache.delete("iclock_"+o.SN)
            o.DelTag=1
            o.save()
#        return models.Model.clear(self)
    def delete(self):
        cache.delete("iclock_"+self.SN)
        self.DelTag=1
        try:
            cache.set("iclock_"+self.SN, self)
            #self.DelTag=1   
        except:
            raise Exception(_(u"Invalid %s")%_(u'serial number'))
        return models.Model.save(self)
    def __unicode__(self):
        return self.SN+(self.Alias and "("+self.Alias+")" or "")
    def clear_device_employee(self):
        return self.SN
    class Admin:
        list_display = ('SN', 'Alias', 'Style', 'LastActivity')
        search_fields = ["SN", "Alias"]
    class Meta:
        db_table = 'iclock'
        verbose_name=_('device')
        verbose_name_plural=verbose_name
        permissions = (
            ('pause_iclock','Pause device'),
            ('resume_iclock','Resume a resumed device'),
            ('upgradefw_iclock','Upgrade firmware'),
            ('copyudata_iclock','Copy data between device'),
            ('reloaddata_iclock','Upload data again'),
            ('reloadlogdata_iclock','Upload transactions again'),
            ('info_iclock','Refresh device information'),
            ('reboot_iclock','Reboot device'),
            ('loaddata_iclock','Upload new data'),
            ('cleardata_iclock','Clear data in device'),
            ('clearlog_iclock','Clear transactions in device'),
            ('devoption_iclock','Set options of device'),
            ('resetPwd_iclock','Reset Password in device'),
            ('restoreData_iclock','Restore employee to device'),
            ('unlock_iclock', 'Output unlock signal'),
            ('unalarm_iclock', 'Terminate alarm signal'),
            ('clear_all_employee','Clear all employee'),
            ('upgrade_by_u-pack','Upgrade by u-pack'),
#            ('',_('')),
        )

def ValidIClocks(qs):
    return qs.filter(Q(DelTag__isnull=True)|Q(DelTag=0)).order_by("Alias")

class DeptAdmin(models.Model):
    user = models.ForeignKey(User)
    dept = models.ForeignKey(department, verbose_name=_('granted department'), null=False, blank=False)
    def __unicode__(self):
        return unicode(self.user)
    class Admin:
        list_display=("user", )
    class Meta:
        verbose_name=_("admin granted department")
        verbose_name_plural=verbose_name
        
def getDevice(n):
    n=n and string.strip(n) or ""
    if not n: return None
    dev=cache.get("iclock_"+n)
    if dev:
        return dev
    try:
        dev=iclock.objects.get(SN=n)
    except ObjectDoesNotExist:
        dev=iclock.objects.get(Alias=n)
    cache.set("iclock_"+n, dev)
    return dev

GENDER_CHOICES = (
    ('M', _('Male')),
    ('F', _('Female')),
)


PRIV_CHOICES=(
    (0,_('Normal')),
    (2,_('Registrar')),
    (6,_('Administrator')),
    (14,_('Supervisor')),
)

def formatPIN(pin):
    if not settings.PIN_WIDTH: return pin
    return string.zfill(devicePIN(pin.rstrip()), settings.PIN_WIDTH)

def devicePIN(pin):
    if not settings.PIN_WIDTH: return pin
    i=0
    for c in pin[0:-1]:
        if c=="0":
            i+=1
        else:
            break
    return pin[i:]

if settings.PIN_WIDTH==5: MAX_PIN_INT=99999#65534
elif settings.PIN_WIDTH==10: MAX_PIN_INT=4294967294L
elif settings.PIN_WIDTH<=1: MAX_PIN_INT=999999999999999999999999L
else: MAX_PIN_INT=int("999999999999999999999999"[:settings.PIN_WIDTH])

CHECK_CLOCK_IN=(
    (0,_('By Time Zone')),
    (1,_('Must Clock In')),
    (2,_('Don\'t Check In')),
)
CHECK_CLOCK_OUT=(
    (0,_('By Time Zone')),
    (1,_('Must Clock Out')),
    (2,_('Don\'t Check Out')),
)


class employee(models.Model):
    id=models.AutoField(db_column="userid", primary_key=True, null=False,editable=False)
    PIN = models.CharField(_('PIN'),db_column="badgenumber",null=False,max_length=20)
    DeptID = models.ForeignKey(department,db_column="defaultdeptid", verbose_name=DEPT_NAME, default=1,editable=True, null=True)
    EName = models.CharField(_('Emp Name'),db_column="name",null=True,max_length=40, blank=True, default=" ")
    Password = models.CharField(_('Password'),max_length=20, null=True, blank=True, editable=True)
    Card = models.CharField(_('ID Card'),max_length=20, null=True, blank=True, editable=True)
    Privilege = models.IntegerField(_('privilege'),null=True, blank=True, choices=PRIV_CHOICES)
    AccGroup = models.IntegerField(_('Access Group'),null=True, blank=True,editable=True)
    TimeZones = models.CharField(_('Access Timezone'),max_length=20, null=True, blank=True,editable=True)
    Gender = models.CharField(_('sex'),max_length=2, choices=GENDER_CHOICES, null=True, blank=True)
    Birthday = models.DateTimeField(_('birthday'),max_length=8, null=True, blank=True)
    Address = models.CharField(_('address'),db_column="street",max_length=40, null=True, blank=True)
    PostCode = models.CharField(_('postcode'),db_column="zip",max_length=6, null=True, blank=True)
    Tele = models.CharField(_('office phone'),db_column="ophone",max_length=20, null=True, blank=True)
    FPHONE=models.CharField(_('home phone'),max_length=20, null=True, blank=True)
    Mobile = models.CharField(_('mobile'),db_column="pager",max_length=20, null=True, blank=True)
    National = models.CharField(_('nationality'),db_column="minzu",max_length=8, null=True, blank=True)
    Title = models.CharField(_('title'),db_column="title",max_length=20, null=True, blank=True)
    SN = models.ForeignKey(iclock, db_column='SN', verbose_name=_('registration device'), null=True, blank=True, editable=True)
    SSN=models.CharField(_('social insurance num'),max_length=20, null=True, blank=True,editable=False)
    UTime = models.DateTimeField(_('refresh time'), null=True, blank=True, editable=False)
    Hiredday=models.DateField(_('participate in the working date'),max_length=8, null=True, blank=True,editable=False)
    VERIFICATIONMETHOD=models.SmallIntegerField(_('verification method'),null=True, blank=True,editable=False)
    State=models.CharField(_('state'),max_length=2, null=True, blank=True,editable=False)
    City=models.CharField(_('city'),max_length=2, null=True, blank=True,editable=False)
    SECURITYFLAGS=models.SmallIntegerField(_('admin flag'),null=True, blank=True,editable=False)
    ATT=models.BooleanField(_('Active AC'),null=True,default=1,  blank=True,editable=False)
    OverTime=models.BooleanField(_('Count OT'),null=True,default=0, blank=True,editable=False)
    Holiday=models.BooleanField(_('Rest on Holidays'),null=True,default=0, blank=True,editable=False)
    INLATE=models.SmallIntegerField(_('Check Clock In'),null=True,default=0, choices=CHECK_CLOCK_IN, blank=True,editable=False)
    OutEarly=models.SmallIntegerField(_('Check Clock Out'),null=True,default=0, choices=CHECK_CLOCK_OUT, blank=True,editable=False)
    Lunchduration=models.SmallIntegerField(_('Lunch'),null=True,default=1, blank=True,editable=False)
    MVerifyPass=models.CharField(_('Password on device'),max_length=2, null=True, blank=True,editable=False)
#    PHOTO=models.TextField(u'照片',null=True,editable=False)
    SEP=models.SmallIntegerField(null=True,default=1,editable=False)
    OffDuty=models.SmallIntegerField(_("left"), null=False, default=0, editable=False, choices=BOOLEANS)
    DelTag=models.SmallIntegerField(null=False,default=0,editable=False)
#    Image = models.ForeignKey(Photo, verbose_name=u'照片', null=True, blank=True)
    AutoSchPlan=models.SmallIntegerField(null=True,default=1,editable=False)
    MinAutoSchInterval=models.IntegerField(null=True,default=24,editable=False)
    RegisterOT=models.IntegerField(null=True,default=1,editable=False)
    @staticmethod
    def objByID(id):
        e=cache.get("%s_iclock_emp_%s"%(settings.UNIT, id))
        if e: return e
        u=employee.objects.get(id=id)
        u.IsNewEmp=False
        cache.set("%s_iclock_emp_%s"%(settings.UNIT,u.id),u)
        cache.set("%s_iclock_emp_PIN_%s"%(settings.UNIT,u.PIN),u)
        return u

    @staticmethod
    def objByPIN(pin, Device):
        #emp=cache.get("%s_iclock_emp_PIN_%s"%(settings.UNIT,pin))
        #if emp: 
        #    return emp
        try:
            emp=employee.objects.get(PIN=pin)
            emp.IsNewEmp=False
        except:                     
            if Device:
                try:
                    deptid=Device.DeptID
                    if not deptid: deptid=getDefaultDept()
                    emp=employee(PIN=pin, EName=" ", DeptID=deptid, SN=Device, UTime=datetime.datetime.now())
                    emp.save()
                    emp.IsNewEmp=True
                except Exception, er:
                    errorLog()
                    raise er
            else:
                raise Exception(_("Employee PIN %s not found")%pin)
        return emp
    def Dept(self): #cached user
        return department.objByID(self.DeptID_id)
    @staticmethod    
    def clear():
        for e in employee.objects.all():
            e.delete()
    def Device(self):
        return getDevice(self.SN_id)
    def getUrl(self):
        return settings.UNIT_URL+"iclock/data/employee/%s/"%self.pk
    def getImgUrl(self, default=None):
        if not self.PIN: return default
        if os.path.exists(getStoredFileName("photo", None, devicePIN(self.PIN)+".jpg")):
            return getStoredFileURL("photo", None, devicePIN(self.PIN)+".jpg")
        return default
    def rmThumbnail(self):
        tbName=getStoredFileName("photo/thumbnail", None, devicePIN(self.PIN)+".jpg")
        if os.path.exists(tbName):
            os.remove(tbName)
    def getThumbnailUrl(self, default=None):
        if not self.PIN: return default
        tbName=getStoredFileName("photo/thumbnail", None, devicePIN(self.PIN)+".jpg")
        tbUrl=getStoredFileURL("photo/thumbnail", None, devicePIN(self.PIN)+".jpg")
        if os.path.exists(tbName):
            return tbUrl
        else:
            fullName=getStoredFileName("photo", None, devicePIN(self.PIN)+".jpg")
            if os.path.exists(fullName):
                if createThumbnail(fullName, tbName):
                    return tbUrl
    def save(self):
        pin_int=int(self.PIN)
        if pin_int in settings.DISABLED_PINS:
            raise Exception(_("Employee PIN '%s' is disabled")%pin_int)
        if pin_int>MAX_PIN_INT:
            raise Exception(_("Max employee PIN is %d")%MAX_PIN_INT)
        self.PIN=formatPIN(self.PIN)
        if not self.id: #new employee
            try:                         
                old=self.objByPIN(self.PIN, None)
            except:
                old=None
            if old:
                raise Exception(_("Duplicated Employee PIN: %s")%self.PIN)
        else: # modify a employee 
            old_emp=self.objByID(self.id)
            if int(old_emp.PIN)<>int(self.PIN): #changed the PIN
                if employee.objects.filter(PIN=self.PIN).count()>0:
                    raise Exception(_("Duplicated Employee PIN: %s")%self.PIN)
        super(employee,self).save()
        cache.set("%s_iclock_emp_%s"%(settings.UNIT,self.id),self)
        cache.set("%s_iclock_emp_PIN_%s"%(settings.UNIT,self.PIN),self)

        return self
    def delete(self):
        try:
            cache.delete("%s_iclock_emp_%s"%(settings.UNIT,self.id))
        except: pass
        try:
            cache.delete("%s_iclock_emp_PIN_%s"%(settings.UNIT,self.PIN))
        except: pass
        super(employee, self).delete()
    def pin(self):
        return devicePIN(self.PIN)
    def fpCount(self):
        return fptemp.objects.filter(UserID=self.id).count()
    def GetCopyFields(self):
        return ["National", "PostCode", "Address", "Gender"]
    def __unicode__(self):
        return self.PIN+(self.EName and " %s"%self.EName or "")
    class Admin:
        list_display=('PIN','EName','DeptID','Gender','Title','Tele','Mobile')
        list_filter = ('DeptID','Gender','SN','UTime',)
        search_fields = ['PIN','EName', 'Tele', 'Mobile']
    class Meta:
        db_table = 'userinfo'
        verbose_name=_("employee")
        verbose_name_plural=verbose_name
        permissions = (
                    ('toDev_employee','Transfer employee to the device'),
                    ('toDevWithin_employee','Transfer to the device templately'),
                    ('delDev_employee','Delete employee from the device'),
                    ('empLeave_employee','Employee leave'),
                    ('mvToDev_employee','Move employee to a new device'),
                    ('toDepart_employee',"Change employee's department"),
                    ('enroll_employee','Enroll employee\'s fingerprint'),
                    ('optionsDatabase_employee','DataBase'),
        )

def getNormalCard(card):
    if not card: return ""    
    try:
        num=int(str(card))
        card="[%02X%02X%02X%02X%02X]"%(num & 0xff, (num >> 8) & 0xff, (num >> 16) & 0xff, (num >> 24) & 0xff, (num >> 32) & 0xff)
    except:
        pass
    return card

def getEmpCmdStr(emp):    
    ename=emp.EName and emp.EName.strip() or ""
    ret= "DATA UPDATE USERINFO PIN=%s\t%s\t%s\t%s\t%s\t%s\tGrp=%s"%(emp.pin(), 
            ename and ("Name=%s"%ename) or "", 
            "Pri=%s"%(emp.Privilege and emp.Privilege or 0), 
            emp.Password and ("Passwd=%s"%emp.Password) or "", 
            emp.Card and ("Card=%s"%getNormalCard(emp.Card)) or "", 
            emp.TimeZones and ("TZ=%s"%emp.TimeZones) or "", 
            emp.AccGroup or 1)
                                        
    return ret                            

FINGERIDS=(
    (0, u'右手食指'),
    (1, u'左手食指'),
    (2, u'右手中指'),
    (3, u'左手中指'),
    (4, u'右手拇指'),
    (5, u'左手拇指'),
    (6, u'右手无名指'),
    (7, u'左手无名指'),
    (8, u'右手小指'),
    (9, u'左手小指'),
)

class fptemp(models.Model):
    id=models.AutoField(db_column='templateid',primary_key=True)
    UserID = models.ForeignKey("employee", db_column='userid', verbose_name=u"员工")
    Template = models.TextField(u'指纹模板')
    FingerID = models.SmallIntegerField(u'手指',default=0, choices=FINGERIDS)
    Valid = models.SmallIntegerField(u'是否有效',default=1, choices=BOOLEANS)
    DelTag = models.SmallIntegerField(u'删除标记',default=0, choices=BOOLEANS)
    SN = models.ForeignKey(iclock, db_column='SN', verbose_name=u'登记设备', null=True, blank=True)
    UTime = models.DateTimeField(_('refresh time'), null=True, blank=True, editable=False)
    BITMAPPICTURE=models.TextField(null=True,editable=False)
    BITMAPPICTURE2=models.TextField(null=True,editable=False)
    BITMAPPICTURE3=models.TextField(null=True,editable=False)
    BITMAPPICTURE4=models.TextField(null=True,editable=False)
    USETYPE = models.SmallIntegerField(null=True,editable=False)
    Template2 = models.TextField(u'指纹模板',null=True,editable=False)
    Template3 = models.TextField(u'指纹模板',null=True,editable=False)
    def __unicode__(self):
        return "%s, %d"%(self.UserID.__unicode__(),self.FingerID)
    def template(self):
        return self.Template.decode("base64")
    def temp(self):
        #去掉BASE64编码的指纹模板中的回车
        return self.Template.replace("\n","").replace("\r","")
    class Admin:
        list_display=('UserID', 'FingerID', 'Valid', 'DelTag')
        list_filter = ('UserID','SN','UTime',)
    class Meta:
        db_table = 'template'
        unique_together = (("UserID", "FingerID"),)
        verbose_name=_("fingerprint")#u"人员指纹"
        verbose_name_plural=verbose_name

VERIFYS=(
#(3, _("Card")),
(0, _("Password")),
(1, _("Fingerprint")),
(2, _("Card")),
#(5, _("Add")),
#(9, _("Other")),
)

ATTSTATES=(
#("0",_("Check in")),
#("1",_("Check out")),
("I",_("Check in")),
("O",_("Check out")),
#("i",_("Break in")),
#("o",_("Break out")),
#("0",_("Check in")),
#("1",_("Check out")),
("2",_("Break out")),
("3",_("Break in")),
("4",_("Overtime in")),
("5",_("Overtime out")),
("8",_("Meal start")),
("9",_("Meal end")),
#("160",_("Test Data")),
)


def createThumbnail(imgUrlOrg, imgUrl):
    try:
        import PIL.Image as Image
    except:
        return None

    try:
        im = Image.open(imgUrlOrg)
    except IOError, e:
        return
    cur_width, cur_height = im.size
    new_width, new_height = 100,75
    if 0: #crop
        if cur_width < cur_height:
            ratio = float(new_width)/cur_width
        else:
            ratio = float(new_height)/cur_height
        x = (cur_width * ratio)
        y = (cur_height * ratio)
        x_diff = int(abs((new_width - x) / 2))
        y_diff = int(abs((new_height - y) / 2))
        box = (x_diff, y_diff, (x-x_diff), (y-y_diff))
        resized = im.resize((x, y), Image.ANTIALIAS).crop(box)
    else:
        if not new_width == 0 and not new_height == 0:
            if cur_width > cur_height:
                ratio = float(new_width)/cur_width
            else:
                ratio = float(new_height)/cur_height
        else:
            if new_width == 0:
                ratio = float(new_height)/cur_height
            else:
                ratio = float(new_width)/cur_width
        resized=im.resize((int(cur_width*ratio), int(cur_height*ratio)), Image.ANTIALIAS)
    try:
        os.makedirs(os.path.split(imgUrl)[0])
    except:
        pass
    resized.save(imgUrl)
    return imgUrl

class transaction(models.Model):
    UserID = models.ForeignKey("employee", db_column='userid', verbose_name=_("employee"))
    TTime = models.DateTimeField(_('time'), db_column='checktime')
    State = models.CharField(_('state'), db_column='checktype', max_length=1, default='I', choices=ATTSTATES)
    Verify = models.IntegerField(_('verification'), db_column='verifycode', default=0, choices=VERIFYS)
    SN = models.ForeignKey(iclock, db_column='SN', verbose_name=_('device'), null=True, blank=True)
    sensorid = models.CharField(db_column='sensorid', verbose_name=u'Sensor ID', null=True, blank=True, max_length=5, editable=False)
    WorkCode = models.CharField(_('work code'), max_length=20, null=True, blank=True)
    Reserved = models.CharField(_('Reserved'), max_length=20, null=True, blank=True)
    def employee(self): #cached employee
        try:
            return employee.objByID(self.UserID_id)
        except:
            return None
    def Time(self):
        if self.TTime.microsecond>500000:
            self.TTime=self.TTime+datetime.timedelta(0,0,1000000-self.TTime.microsecond)
        return self.TTime
    def StrTime(self):
        return self.Time().strftime('%Y/%m%d/%H%M%S')
    @staticmethod    
    def delOld(): return ("TTime", 365)
    def Device(self):
        return getDevice(self.SN_id)
    def getImgUrl(self, default=None):
        device=self.Device()
        emp=self.employee()
        if device and emp:
            try:
                pin=int(emp.PIN)
            except:
                pin=emp.PIN
            fname="%s.jpg"%(self.StrTime())
            imgUrl=getUploadFileName(device.SN, pin, fname)
            if os.path.exists(imgUrl):
                return getUploadFileURL(device.SN, pin, fname)
        return default
    def getThumbnailUrl(self, default=None):
        device=self.Device()
        emp=self.employee()
        if device and emp:
            try:
                pin=int(emp.PIN)
            except:
                pin=emp.PIN
            fname="%s.jpg"%(self.StrTime())
            imgUrl=getUploadFileName("thumbnail/"+device.SN, pin, fname)
            if not os.path.exists(imgUrl):
                imgUrlOrg=getUploadFileName(device.SN, pin, fname)
                if not os.path.exists(imgUrlOrg):
                    return default
                if not createThumbnail(imgUrlOrg, imgUrl):
                    return default
            return getUploadFileURL("thumbnail/"+device.SN, pin, fname)
        return default
    def __unicode__(self):
        return self.UserID.__unicode__()+', '+self.TTime.strftime("%y-%m-%d %H:%M:%S")
    class Meta:
        verbose_name=_("transaction")
        verbose_name_plural=_("transactions")
        db_table = 'checkinout'
        unique_together = (("UserID", "TTime"),)
        permissions = (
                ('clearObsoleteData_transaction','Clear Obsolete Data'),
                )
        
    class Admin:
        list_display=('UserID','TTime','State','Verify','SN')
        list_filter = ('UserID','TTime','State','Verify','SN',)
        
        

def OpName(op):
    OPNAMES={0: _("start up"),
        1: _("shutdown"),
        2: _("validation failure"),
        3: _("alarm"),
        4: _("enter the menu"),
        5: _("change settings"),
        6: _("registration fingerprint"),
        7: _("registration password"),
        8: _("card registration"),
        9: _("delete User"),
        10: _("delete fingerprints"),
        11: _("delete the password"),
        12: _("delete RF card"),
        13: _("remove data"),
        14: _("MF create cards"),
        15: _("MF registration cards"),
        16: _("MF registration cards"),
        17: _("MF registration card deleted"),
        18: _("MF clearance card content"),
        19: _("moved to the registration card data"),
        20: _("the data in the card copied to the machine"),
        21: _("set time"),
        22: _("restore factory settings"),
        23: _("delete records access"),
        24: _("remove administrator rights"),
        25: _("group set up to amend Access"),
        26: _("modify user access control settings"),
        27: _("access time to amend paragraph"),
        28: _("amend unlock Portfolio"),
        29: _("unlock"),
        30: _("registration of new users"),
        31: _("fingerprint attribute changes"),
        32: _("stress alarm"),
        } #{0: u"开机",
        #1: u"关机",
        #2: u"验证失败",
        #3: u"报警",
        #4: u"进入菜单",
        #5: u"更改设置",
        #6: u"登记指纹",
        #7: u"登记密码",
        #8: u"登记HID卡",
        #9: u"删除用户",
        #10: u"删除指纹",
        #11: u"删除密码",
        #12: u"删除射频卡",
        #13: u"清除数据",
        #14: u"创建MF卡",
        #15: u"登记MF卡",
        #16: u"注册MF卡",
        #17: u"删除MF卡注册",
        #18: u"清除MF卡内容",
        #19: u"把登记数据移到卡中",
        #20: u"把卡中的数据复制到机器中",
        #21: u"设置时间",
        #22: u"恢复出厂设置",
        #23: u"删除进出记录",
        #24: u"清除管理员权限}",
        #25: u"修改门禁组设置",
        #26: u"修改用户门禁设置",
        #27: u"修改门禁时间段",
        #28: u"修改开锁组合设置",
        #29: u"开锁",
        #30: u"登记新用户",
        #31: u"更改指纹属性",
        #32: u"胁迫报警",    
    try:
        return OPNAMES[op]
    except:
        return op and "%s"%op or ""
        
def AlarmName(obj):
    ALARMNAMES={
        50:_("Door Close Detected"),
        51:_("Door Open Detected"),
        55:_("Machine Been Broken"),
        53:_("Out Door Button"),
        54:_("Door Broken Accidentally"),
        58:_("Try Invalid Verification"),
        65535:_("Alarm Cancelled"),
    }
    try:
        return ALARMNAMES[obj]
    except:
        return obj and "%s"%obj or ""

                                                               
class oplog(models.Model):
    SN = models.ForeignKey(iclock, db_column='SN', verbose_name=_('device'), null=True, blank=True)
    admin = models.IntegerField(_('device administrator'), null=False, blank=False, default=0)
    OP = models.SmallIntegerField(_('Operation'), null=False, blank=False, default=0)
    OPTime=models.DateTimeField(_('time'))
    Object=models.IntegerField(_('Object'), null=True, blank=True)
    Param1=models.IntegerField(_('Parameter1'), null=True, blank=True)
    Param2=models.IntegerField(_('Parameter2'), null=True, blank=True)
    Param3=models.IntegerField(_('Parameter3'), null=True, blank=True)
    def Device(self):
        return getDevice(self.SN_id)
    @staticmethod    
    def delOld(): return ("OPTime", 200)
    def OpName(self):
        return OpName(self.OP)
    def ObjName(self):
        if self.OP==3:
            return AlarmName(self.Object)
        return self.Object or ""
    def __unicode__(self):
        return "%s,%s,%s"%(self.Device(), self.OP, self.OPTime.strftime("%y-%m-%d %H:%M:%S"))
    class Meta:
        verbose_name=_("device operation log")
        verbose_name_plural=_("device operation logs")
        unique_together = (("SN", "OPTime"),)
        permissions = (
            ('monitor_oplog', 'Transaction Monitor'),
            )
    class Admin:
        list_display=('SN','admin','OP','OPTime', 'Object',)
        list_filter = ('SN','admin','OP','OPTime')

class devlog(models.Model):
    SN = models.ForeignKey(iclock, verbose_name=_('device'))
    OP = models.CharField(_('data'),max_length=8, default="TRANSACT",)
    Object = models.CharField(_('object'),max_length=20, null=True, blank=True)
    Cnt = models.IntegerField(_('record count'),default=1, blank=True)
    ECnt = models.IntegerField(_('error count'),default=0, blank=True)
    OpTime = models.DateTimeField(_('Upload Time'),default=datetime.datetime.now())
    def Device(self):
        return getDevice(self.SN_id)
    @staticmethod    
    def delOld(): return ("OpTime", 30)
    def save(self):
        if not self.id:
            self.OpTime=datetime.datetime.now()
        models.Model.save(self)
    def __unicode__(self): return "%s, %s, %s"%(self.SN, self.OpTime.strftime('%y-%m-%d %H:%M'), self.OP)
    class Admin:
        list_display=('SN','OpTime','OP','Cnt','Object',)
        list_filter=("SN",'OpTime')
        search_fields = ["OP","Object"]
    class Meta:
        verbose_name=_("data from device")
        verbose_name_plural=verbose_name
        db_table = 'devlog'

def getStoredFileName(sn, id, fname):
    fname="%s%s/%s"%(settings.ADDITION_FILE_ROOT, sn, fname)
    if id:
        fname, ext=os.path.splitext(fname)
        fname="%s_%s%s"%(fname,id,ext)
    fname.replace("\\\\","/")
    return fname
def getStoredFileURL(sn, id, fname):
    fname="/iclock/file/%s/%s"%(sn, fname)
    if id:
        fname, ext=os.path.splitext(fname)
        fname="%s_%s%s"%(fname,id,ext)
    return fname

def getUploadFileName(sn, id, fname):
    return getStoredFileName('upload/'+sn, id, fname)
def getUploadFileURL(sn, id, fname):
    return getStoredFileURL('upload/'+sn, id, fname)

class devcmds(models.Model):
    SN = models.ForeignKey("iclock", verbose_name=_('device'))
    #UserName = models.CharField('提交用户',max_length=20,null=True, blank=True)
    CmdContent = models.TextField(_('command content'),max_length=2048)
    CmdCommitTime = models.DateTimeField(_('submit time'),default=datetime.datetime.now())
    CmdTransTime = models.DateTimeField(_('transfer time'),null=True, blank=True)
    CmdOverTime = models.DateTimeField(_('return time'),null=True, blank=True)
    CmdReturn = models.IntegerField(_('return value'), null=True, blank=True)
    User = models.ForeignKey(User, verbose_name=_('administrator'), null=True, blank=True, editable=False) 
    def Device(self):
        return getDevice(self.SN_id)
    def __unicode__(self): return "%s, %s" % (self.SN, self.CmdCommitTime.strftime('%y-%m-%d %H:%M'))
    def save(self, raw=None):
        if self.SN and not self.CmdTransTime: deviceHasCmd(self.SN)
        return models.Model.save(self)
    def fileURL(self):
        if self.CmdContent.find("GetFile ")==0:
            fname=self.CmdContent[8:]
        elif self.CmdContent.find("Shell ")==0:
            fname="shellout.txt"
        else:
            return ""
        return getUploadFileURL(self.SN.SN, self.id, fname)
    @staticmethod    
    def delOld(): return ("CmdOverTime", 10)
    class Admin:
        list_display=('SN','CmdCommitTime','CmdTransTime','CmdOverTime','CmdContent',)
        search_fields = ["CmdContent"]
        list_filter =['SN', 'CmdCommitTime', 'CmdOverTime','CmdReturn']
    class Meta:
        db_table = 'devcmds'
        verbose_name=_("command to device")
        verbose_name_plural=verbose_name

def isUpdatingFW(device):
    return devcmds.objects.filter(SN=device, CmdReturn__isnull=True, CmdContent__startswith='PutFile ', CmdContent__endswith='main.gz.tmp',).count()

def clearData():
    for obj in employee.objects.all(): obj.delete()
    for obj in devcmds.objects.all():
        obj.CmdOverTime=None
        obj.CmdTransTime=None
        obj.save()
    for obj in iclock.objects.all():
        obj.LogStamp=1
        obj.OpLogStamp=1
        obj.save()



#Iclock 信息订阅服务

M_WEATHER=1
M_NEWS=2
M_DEPT_NOTES=3
M_SYS_NOTES=4
M_DEPT_SMS=6
M_PRIV_SMS=5

PUBMSGSERVICES=(
(M_NEWS, _("News Channel")),
(M_DEPT_NOTES, _("Company Notice")),
(M_SYS_NOTES, _("Notice System")),
(M_DEPT_SMS, _("Companies short message")),
)

MSGSERVICES=(
(M_WEATHER, _("Weather Forecast")),
(M_PRIV_SMS, _("Employee SMS")),
(M_NEWS, _("News Channel")),
(M_DEPT_NOTES, _("Company Notice")),
(M_SYS_NOTES, _("System Notice")),
(M_DEPT_SMS, _("Companies SMS")),
)

class messages(models.Model):
    MsgType = models.IntegerField(_("type"), null=False, blank=False, default=5, choices=PUBMSGSERVICES)
    StartTime = models.DateTimeField(_("take effect"), null=False, blank=False, default=datetime.datetime.now())
    EndTime    = models.DateTimeField(_("out-of-service"), null=True, blank=True)   
    MsgContent = models.TextField(_("Content"), max_length=2048, null=True, blank=True)
    MsgImage = models.CharField(_("picture"), max_length=64, null=True, blank=True)
    DeptID = models.ForeignKey(department, verbose_name=_('company/department'), null=True, blank=True)
    MsgParam = models.CharField(_("parameter"), max_length=32, null=True, blank=True)
    def __unicode__(self):
        return unicode(u"%s[%s]: %s"%(self.get_MsgType_display(), self.StartTime, self.MsgContent and self.MsgContent[:40] and ''))
    class Admin:
        list_filter =['StartTime','MsgType', 'MsgParam', 'DeptID']
    class Meta:
        verbose_name=_("public information")
        verbose_name_plural=verbose_name


class IclockMsg(models.Model):
    SN = models.ForeignKey(iclock, verbose_name=_('device'), null=False, blank=False)
    MsgType = models.IntegerField(_("type"), null=False, blank=False, default=5, choices=MSGSERVICES)
    StartTime = models.DateTimeField(_("take effect"), null=False, blank=False, default=datetime.datetime.now())
    EndTime    = models.DateTimeField(_("out-of-service"), null=True, blank=True)   
    MsgParam = models.CharField(_("parameter"), max_length=32, null=True, blank=True)
    MsgContent = models.CharField(_("content"), max_length=200, null=True, blank=True)
    LastTime = models.DateTimeField(_("recently service"), null=True, blank=True, editable=False)
    def Device(self):
        return getDevice(self.SN_id)
    def __unicode__(self):
        return unicode(u"%s"%(self.SN))
    class Admin:
        list_filter =['SN','MsgType','StartTime','EndTime']
    class Meta:
        verbose_name=_("information subscription")
        verbose_name_plural=verbose_name

class adminLog(models.Model):
    time = models.DateTimeField(_('time'), default=datetime.datetime.now(), null=False, blank=False)
    User = models.ForeignKey(User, verbose_name=_('administrator'), null=True, blank=True) 
    model = models.CharField(_('data'), max_length=40, null=True, blank=True)                                              
    action = models.CharField(_('operation'), max_length=40, default="Modify", null=False, blank=False)
    object = models.CharField(_('object'), max_length=40, null=True, blank=True)
    count = models.IntegerField(_('amount'), default=1, null=False, blank=False)
    @staticmethod    
    def delOld(): return ("time", 200)
    def save(self):
        if not self.id: self.time=datetime.datetime.now()
        models.Model.save(self)
    def __unicode__(self):
        return unicode(u"[%s]%s, %s"%(self.time, self.User.username, self.action))
    class Admin:
        list_filter =['time','User','model']
    class Meta:
        verbose_name=_("administration log")
        verbose_name_plural=_("administration logs")

def delOldRecords(model, field, days):
    table=model._meta.db_table
    field=model._meta.get_field(field).column
    cursor = connection.cursor()
    cursor.execute("DELETE FROM %s WHERE %s < %%s"%(table, field), [str(datetime.datetime.now()-datetime.timedelta(days))])
    connection._commit()                                             
#    for t in adminLog.objects.filter(time__lt=datetime.datetime.now()-datetime.timedelta(200)):
#        t.delete()
                                                    




def customSql(sql,action=True):
#    from django.db import connection
    cursor = connection.cursor()
    
    cursor.execute(sql)
    if action:
        connection._commit()
    return cursor

       
def batchSql(sqls):
    for s in sqls:
        try:
            customSql(s)
            connection._commit()
        except:
            try:
                connection.close()
                customSql(s)
            except Exception, e:
                pass

def createDefautValue():
    sqls=(
"ALTER TABLE departments ADD CONSTRAINT sdf DEFAULT 1 FOR supdeptid",
"ALTER TABLE userinfo ADD CONSTRAINT ddf DEFAULT 1 FOR defaultdeptid",
"ALTER TABLE userinfo ADD CONSTRAINT tdf DEFAULT 1 FOR ATT",
"ALTER TABLE userinfo ADD CONSTRAINT indf DEFAULT 1 FOR INLATE",
"ALTER TABLE userinfo ADD CONSTRAINT oedf DEFAULT 1 FOR OutEarly",
"ALTER TABLE userinfo ADD CONSTRAINT otdf DEFAULT 1 FOR OverTime",
"ALTER TABLE userinfo ADD CONSTRAINT hdf DEFAULT 1 FOR Holiday",
"ALTER TABLE userinfo ADD CONSTRAINT ldf DEFAULT 1 FOR Lunchduration",
"ALTER TABLE userinfo ADD CONSTRAINT sepdf DEFAULT 1 FOR SEP",
"ALTER TABLE userinfo ADD CONSTRAINT offdutydf DEFAULT 0 FOR OffDuty",
"ALTER TABLE userinfo ADD CONSTRAINT DelTagdf DEFAULT 0 FOR DelTag",
"ALTER TABLE userinfo ADD CONSTRAINT enamedf DEFAULT ' ' FOR name",
"ALTER TABLE template ADD CONSTRAINT fiddf DEFAULT 0 FOR FingerID",
"ALTER TABLE template ADD CONSTRAINT vdf DEFAULT 1 FOR Valid",
"ALTER TABLE template ADD CONSTRAINT dtdf DEFAULT 0 FOR DelTag",
"ALTER TABLE checkinout ADD CONSTRAINT stdf DEFAULT 'I' FOR checktype",
"ALTER TABLE checkinout ADD CONSTRAINT vcedf DEFAULT 0 FOR verifycode",
"CREATE UNIQUE INDEX USERFINGER ON TEMPLATE(USERID, FINGERID)",
"CREATE INDEX DEPTNAME ON DEPARTMENTS(DEPTNAME)",
"CREATE UNIQUE INDEX EXCNOTE ON EXCNOTES(USERID, ATTDATE)",
"ALTER TABLE iclock ADD CONSTRAINT accfundf DEFAULT 0 FOR AccFun",
"ALTER TABLE iclock ADD CONSTRAINT tzadjdf DEFAULT 8 FOR TZAdj",
    )
    batchSql(sqls);


def tryAddPermission(ct, cn, cname):
    try:
        Permission.objects.get(content_type=ct, codename=cn)
    except:
        try:
            Permission(content_type=ct, codename=cn, name=cname).save()
            print "Add permission %s OK"%cn
        except Exception, e:
            print "Add permission %s failed:"%cn, e

def checkAndCreateModelPermission(model):
    ct=ContentType.objects.get_for_model(model)

    cn='browse_'+model.__name__.lower()
    cname='Can browse %s'%model.__name__
    tryAddPermission(ct, cn, cname)
    for perm in model._meta.permissions:
        tryAddPermission(ct, perm[0], perm[1])

def checkAndCreateModelPermissions(appName):
    from django.db.models.loading import get_app
    from django.db import models
    app=get_app(appName)
    for i in dir(app):
        try:
            a=app.__getattribute__(i)
            if issubclass(a, models.Model):
                checkAndCreateModelPermission(a)
        except:
            pass
    try:
        ct=ContentType.objects.get_for_model(transaction)
        Permission(content_type=ct, codename='init_database', name='Init database').save()
    except: pass
    try:        
        ct=ContentType.objects.get_for_model(Group)
        Permission(content_type=ct, codename='browse_'+Group.__name__.lower(), name='Can browse %s'%Group.__name__).save()
    except: pass

def __permission_unicode__(self):
    ct_id=self.content_type_id
    ckey="%s_ct_%s"%(settings.UNIT,ct_id)
    ct=cache.get(ckey)
    if not ct:
        ct=self.content_type
        cache.set(ckey, ct, 60*30)
    return u"%s | %s | %s" % (
        unicode(ct.app_label),
        unicode(ct),
        unicode(self.name))

Permission.__unicode__=__permission_unicode__

def __mci_init__(self, field):
    self.field = field
    q=[]
    for obj in field.queryset.all():
        q.append(obj)
    self.queryset=q

def __mci_iter__(self):
    if self.field.empty_label is not None:
        yield (u"", self.field.empty_label)
    if self.field.cache_choices:
        if self.field.choice_cache is None:
            self.field.choice_cache = [
                self.choice(obj) for obj in self.queryset
            ]
        for choice in self.field.choice_cache:
            yield choice
    else:
        for obj in self.queryset:
            yield self.choice(obj)

if settings.DATABASE_ENGINE=="ado_mssql":
    ModelChoiceIterator.__init__=__mci_init__
    ModelChoiceIterator.__iter__=__mci_iter__

def upgradeDB():
    sqls=(
    "ALTER TABLE userinfo ADD AutoSchPlan int NULL",
    "ALTER TABLE userinfo ADD MinAutoSchInterval int NULL",
    "ALTER TABLE userinfo ADD RegisterOT int NULL",
    "ALTER TABLE userinfo ADD Image_id int NULL",
    "ALTER TABLE iclock ADD PhotoStamp varchar(20) NULL",
    "ALTER TABLE iclock ADD FWVersion varchar(30) NULL",
    "ALTER TABLE iclock ADD FPCount varchar(10) NULL",
    "ALTER TABLE iclock ADD TransactionCount varchar(10) NULL",
    "ALTER TABLE iclock ADD UserCount varchar(10) NULL",
    "ALTER TABLE iclock ADD MainTime varchar(20) NULL",
    "ALTER TABLE iclock ADD MaxFingerCount int NULL",
    "ALTER TABLE iclock ADD MaxAttLogCount int NULL",
    "ALTER TABLE iclock ADD DeviceName varchar(30) NULL",
    "ALTER TABLE iclock ADD AlgVer varchar(30) NULL",
    "ALTER TABLE iclock ADD FlashSize varchar(10) NULL",
    "ALTER TABLE iclock ADD FreeFlashSize varchar(10) NULL",
    "ALTER TABLE iclock ADD Language varchar(30) NULL",
    "ALTER TABLE iclock ADD VOLUME varchar(10) NULL",
    "ALTER TABLE iclock ADD DtFmt varchar(10) NULL",
    "ALTER TABLE iclock ADD IPAddress varchar(20) NULL",
    "ALTER TABLE iclock ADD IsTFT varchar(5) NULL",
    "ALTER TABLE iclock ADD Platform varchar(20) NULL",
    "ALTER TABLE iclock ADD Brightness varchar(5) NULL",
    "ALTER TABLE iclock ADD BackupDev varchar(30) NULL",
    "ALTER TABLE iclock ADD OEMVendor varchar(30) NULL",
    "ALTER TABLE iclock ADD AccFun int NOT NULL DEFAULT 0",
    "ALTER TABLE iclock ADD TZAdj int NOT NULL DEFAULT 8",
    "ALTER TABLE checkinout ADD WorkCode VARCHAR(20) NULL",
    "ALTER TABLE checkinout ADD Reserved VARCHAR(20) NULL",
    "ALTER TABLE iclock DROP COLUMN CheckInterval")
    batchSql(sqls)
    from mysite.iclock.modpin import checkPINWidth
    checkPINWidth()                                        

def initDB():
    try:
        checkAndCreateModelPermissions(iclock._meta.app_label)
    except: pass

    upgradeDB()
    createDefautValue()
#    return
    if department.objects.all().count()==0:
        department(DeptName='Our Company', DeptID=1).save()




