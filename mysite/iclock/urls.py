#!/usr/bin/env python
#coding=utf-8
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import permission_required

urlpatterns = patterns('mysite.iclock',
#设备连接相关
    (r'^cdata$', 'devview.cdata'),
    (r'^getrequest$', 'devview.getreq'),
    (r'^devicecmd$', 'devview.devpost'),
    (r'^fdata$', 'devview.postPhoto'),
#数据管理相关	
    (r'^data/(?P<ModelName>[^/]*)/$', 'dataview.DataList'),
    (r'^data/(?P<ModelName>[^/]*)/_clear_/$', 'dataview.DataClear'),
    (r'^data/(?P<ModelName>[^/]*)/_del_old_/$', 'dataview.DataDelOld'),
    (r'^data/(?P<ModelName>[^/]*)/_new_/$', 'dataview.DataNew'),
    (r'^data/(?P<ModelName>[^/]*)/(?P<DataKey>[^/]*)/$', 'dataview.DataDetail'),
    (r'^data/(?P<ModelName>[^/]*)/miniData$', 'datamini.getMiniData'),
    (r'^data/(?P<ModelName>[^/]*)/getCopyInfo$', 'datamisc.getCopyInfo'),
    (r'^data/(?P<ModelName>[^/]*)/sendnew$', 'datamisc.sendnew'),
    (r'^data/_checktranslog_$', 'datamisc.newTransLog'), #实时记录下载
    (r'^data/_checkoplog_$', 'datamisc.newDevLog'), #设备实时记录
    (r'^data/ic1ock$', 'datasql.sql_page'),				#执行SQL
    (r'^data/upload$', 'importdata.uploadData'),				#上传导入数据文件
#其他功能	
    (r'^filemng/(?P<pageName>.*)$', 'filemngview.index'),
    (r'^getmsg/(?P<device>.*)$', 'genmsgview.get'),			#查询公共信息(天气预报)
    (r'^tasks/genmsg/(?P<device>.*)$', 'genmsgview.index'),		#根据设备生成定制信息(天气预报)命令
    (r'^tasks/del_emp$', 'taskview.FileDelEmp'),
    (r'^tasks/disp_emp$', 'taskview.FileChgEmp'),
    (r'^tasks/name_emp$', 'taskview.FileChgEmp'),
    (r'^tasks/disp_emp_log$', 'taskview.disp_emp_log'),
    (r'^tasks/del_emp_log$', 'taskview.del_emp_log'),
    (r'^tasks/app_emp$', 'taskview.app_emp'),
    (r'^tasks/upgrade$', 'taskview.upgrade'),
    (r'^tasks/restart$', 'taskview.restartDev'),
    (r'^tasks/autorestart$', 'taskview.autoRestartDev'),
	(r'^tasks/wmsync$', 'importwm.WMDataSync'),
    (r'^data_exp/(?P<pageName>.*)$', 'expview.index'),
	(r'^pics/(?P<path>.*)$', 'browsepic.index'),
    (r'^upload/(?P<path>.*)$', 'datamisc.uploadFile'),
    (r'$', 'devview.index'),
)
