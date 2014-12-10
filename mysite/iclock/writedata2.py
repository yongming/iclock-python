# -*- coding: utf-8 -*-
from django.conf import settings
if settings.DATABASE_ENGINE=='pool':
    settings.DATABASE_ENGINE=settings.POOL_DATABASE_ENGINE
    
from models import *
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
import string
import datetime
import time,os
from mysite.utils import *
from devview import lineToLog, getDevice
from devview import commitLog as cld
from devview import lineToUser
from django.db import IntegrityError
from traceback import print_exc

def commitLog(conn, cursor, sql):
    try:
        cld(cursor, sql, conn)
    except IntegrityError:
        return cursor
    except:
        conn.close()
        cursor=conn.cursor()
        cld(cursor, sql, conn)
    return cursor

def parseAOpLogData(device, conn, cursor, lines):
    print "parseAOpLogData"

def parseATransLogData(device, conn, cursor, lines):
    print 'parseATransLogData'

def parseATransData(conn, cursor, lines):
    l=lines[0]
    sn=l.split("SN=")[1].split("\t")[0]
    try:
        device=getDevice(sn)
    except:
        device=None
    if device is None:
        print "UNKOWN Device: ", sn
    elif ":TRANSACTIONS:" in l:
        return parseATransLogData(device, conn, cursor, lines[1:])
    elif ":OPLOG:" in l:
        return parseAOpLogData(device, conn, cursor, lines[1:])
    else:
        print "UNKOWN DATA", lines
    return (len(lines), 0)
    

def parseLogDataInFile(conn, cursor):
    print 'start parseLogDataInFile----------------------------------------------'
    start_time=time.time()
    i=0
    lc=0
    tmp_dir=tmpDir()
    while True:
        if time.time()-start_time>10*60: #max live 10 minutes
            break;
        fcount=0
        files=os.listdir(tmp_dir+"\\read")
        for file_name in files:
            if file_name[-4:]==".txt":
                tmp_file="%s\\read\\%s"%(tmp_dir, file_name)
                print "read data file: ", tmp_file
                try:
                    lines=file(tmp_file, "rb").read()
                except:
                    continue
                if lines:
                    now=datetime.datetime.now()
                    new_file="%s\\write\\%s\\%s"%(tmp_dir, now.strftime("%Y%m%d"), file_name)
                try:
                    os.renames(tmp_file, new_file)
                except:
                    try:
                        os.remove(tmp_file)
                    except: pass
                fcount+=1
        if fcount==0:
            print "no transactions in the directory"
            time.sleep(10)
        
        #if lc>50000: #太多记录，退出，下一次再继续
            #break;
    print "lines: %s, valid: %s, seconds: %s"%(lc, i, int(time.time()-start_time))
    return i

                  
def parseLogDataInQueqe(conn, cursor, q_server):
    start_time=time.time()
    i=0
    lc=0
    while True:
        if time.time()-start_time>10*60: #max live 10 minutes
            break;
        try:
            lines=q_server.rpop("TRANS")
        except Exception, e:
            time.sleep(1);            
            continue
        if not lines:
            print "no transactions in the queqe"
            time.sleep(5);
            continue
        if lines:
            lcc, okc=parseATransData(conn, cursor, lines.decode("utf-8").splitlines())
            lc+=lcc
            i+=okc
        if lc>50000: #太多记录，退出，下一次再继续
            break;
    print "lines: %s, valid: %s, seconds: %s"%(lc, i, int(time.time()-start_time))
    return i
    

def performPostDataFile_(count=5):
    wt=[]
    for i in range(count):
        t=WriteDataThread(i)
        wt.append(t)
        t.start()
        time.sleep(1)
    while False:
        time.sleep(1)
        all_finished=True
        for t in wt:
            if t.isAlive(): 
                all_finished=False
                break
        if all_finished: 
            break

def run_writedata(index=0):
        from django.db import backend
        connection = backend.DatabaseWrapper(**settings.DATABASE_OPTIONS)
        q=queqe_server()
        cursor=connection.cursor()
        print "-----------------------Start Writedata %s"%index
        parseLogDataInFile(connection, cursor)
        try:
            cursor.close()
            connection.close()
        except: pass
        q.connection.disconnect()
        print "-----------------------End Writedata %s"%index


class WriteDataThread(threading.Thread):
    def __init__(self, index):
        self.index=index
        super(WriteDataThread, self).__init__()
    def run(self):
        run_writedata(self.index)

def performPostDataFile(count=5):
    run_writedata(0)
