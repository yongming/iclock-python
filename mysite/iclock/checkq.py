# -*- coding: utf-8 -*-

from django.conf import settings
if settings.DATABASE_ENGINE=='pool':
    settings.DATABASE_ENGINE=settings.POOL_DATABASE_ENGINE

from redis.server import queqe_server, start_q_server
from models import iclock, devcmds, triggerCmdDevice, getDevice
from django.db import connection
from django.db.models import Q
import datetime
import time
from django.http import HttpResponse

def del_old_cmd():
    cursor=connection.cursor()
    cursor.execute("delete from %s where CmdCommitTime<'%s'"%(devcmds._meta.db_table, (datetime.datetime.now()-datetime.timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")))
    connection._commit()

def check_cmd_queqe_by_device(device):
    new_cmds=device.get_new_command_list()
    cmd_ids=device.get_processing_commands()
    hours2=datetime.datetime.now()-datetime.timedelta(hours=2)
    days60=datetime.datetime.now()-datetime.timedelta(days=60)
    for cmd in device.devcmds_set.filter(CmdOverTime__isnull=True, CmdCommitTime__gte=days60, pk__gt==device.last_cmd_id).order_by("id"):
        new=False
        if (cmd.CmdTransTime is None) or (cmd.CmdTransTime<hours2):
            new=True
        elif cmd.pk not in cmd_ids:
            new=True
        if new and not cmd.pk in new_cmds:
            new_cmds.append(str(cmd.pk))
    l=len(new_cmds)
    device.new_command_list=",".join(new_cmds)
    print "\tCMDS:", l 
    return l


def check_cmd_queqe_by_cmd_(q_server):
    devices={} #已清理过的设备
    hours2=datetime.datetime.now()-datetime.timedelta(hours=2)
    days60=datetime.datetime.now()-datetime.timedelta(days=60)
    l=0
    for cmd in devcmds.objects.filter(CmdOverTime__isnull=True, CmdCommitTime__gte=days60).filter(Q(CmdTransTime__isnull=True)|Q(CmdTransTime__lte=hours2)).order_by("id"):
        sn=cmd.SN_id
        if sn not in devices: #还没有清理过的设备
            device=getDevice(sn)
            new_cmds=device.new_command_list_name() 
            q_server.delete(new_cmds)   #删除掉设备命令队列
            devices[sn]=device   #放入已清理过的设备列表
        else:
            device=devices[sn]
        cmd.SN=device #避免查询数据库
        triggerCmdDevice(cmd, q_server) #重新把命令放入队列中
        l+=1
    return l

#检查并同步数据库中的设备命令到队列
def check_cmd_queqe_by_cmd(q_server):
    now=int(time.time())
    last=q_server.get("LAST_CHECK_CMD_Q")
    if (last is None) or (now-int(last)>5*60): #5分钟从数据库同步到队列
        print "last sync commands at %s, need sync again"%last
        check_cmd_queqe_by_cmd_(q_server)
        q_server.set("LAST_CHECK_CMD_Q", now)

def check_queqe_server(request=None):
    del_old_cmd()
    q_server=queqe_server()
    old_size=q_server.dbsize()
    sql_return=q_server.keys("sql_execute_*")
    if sql_return: q_server.delete(*sql_return)
    #q_server.flushall()
    q_server.bgsave()
    for i in iclock.objects.all():
        check_cmd_queqe_by_device(i, q_server)
    info="OK, keys in db: %s -> %s"%(old_size,q_server.dbsize())
    if request:
        return HttpResponse(info)
    return info


