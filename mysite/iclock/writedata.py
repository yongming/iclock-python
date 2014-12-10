# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.encoding import smart_str

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
        pass
    except Exception,ex:
        raise ex
    except:
        print_exc()
        print "try again"
        conn._rollback()
        conn.close()
        cursor=conn.cursor()
        cld(cursor, sql, conn)
    return cursor

def parseAOpLogData(device, conn, cursor, lines):
    print "user or op lines count:", len(lines)
    c=0;
    ec=0;
    try:
        user=False
        for line in lines:
            try:
                if line:
                    user=lineToUser(cursor,device,line)
                    c=c+1
            except Exception,e:
                ec=ec+1
                appendFile("ERROR(cdata-writedata):%s\nLine:%s"%(e,line))
        try:
            conn._commit()
        except:
            print_exc()
        dlogObj="TMP"
        try:
            dlogObj=(u"%s"%user)[:20]
        except: pass
        devlog(SN=device, Cnt=c, OP=u"USERDATA", ECnt=ec, Object=dlogObj, OpTime=datetime.datetime.now()).save()
    except Exception, e:
        print_exc()
    return c+ec, c

def parseATransLogData(device, conn, cursor, lines):
    print "trans lines count:", len(lines)
    okc=0;
    errorLogs=[]  #解析出错、不正确数据的行
    errorLines=[] #发生保存错误的记录
    cacheLines=[] #本次提交的行
    sqls=[]
    lc=0
    for l in lines:
        if not l:
            break
        lc+=1
        eMsg=""; alog=""
        try:
            log=lineToLog(device, l)
        except Exception, e:
            eMsg=u"%s"%e
            errorLogs.append("%s\t--%s"%(l, eMsg))
            log=None
        if log:
            sqls.append(log)
            cacheLines.append(l) #先记住还没有提交数据，commit不成功的话可以知道哪些数据没有提交成功
            print "len cache lines count : %s"%len(cacheLines)
            if len(cacheLines)>=700: #达到700行就提交一次
                try:
                    cursor=commitLog(conn, cursor, sqls)
                    okc+=len(cacheLines)
                    print "\tcommit ", len(cacheLines)
                    alog=cacheLines[0]
                except:
                    errorLines+=cacheLines
                cacheLines=[]
                sqls=[]
#            else:
#                 errorLogs.append("%s\t--%s"%(l, eMsg and eMsg or "Invalid Data"))
    #数据分析已经完成
    if cacheLines: #有还没有提交的数据
        try:
            cursor=commitLog(conn, cursor, sqls)
            okc+=len(cacheLines)
            print "\tcommit last:", len(cacheLines)
            if not alog:
                alog=cacheLines[0]
        except:
            print_exc()
            errorLines+=cacheLines
    if errorLines: #重新保存上面提交失败的数据，每条记录提交一次，最小化失败记录数
        cacheLines=errorLines
        errorLines=[]
        for line in cacheLines:
            if line not in errorLogs:
                try:
                    log=lineToLog(device, line)
                    cursor=commitLog(conn, cursor, log)
                    okc+=1
                    print "\tcommit last error:", line
                except Exception, e:
                    eMsg=u"%s"%e
                    if "Duplicate" not in eMsg:
                        errorLines.append("%s\t--%s"%(line, eMsg))
    errorLines+=errorLogs
    dlogObj=""
    try:
        if okc==1:
            dlogObj=alog
        elif okc>1:
            dlogObj=alog + ", ..."
    except Exception,e:
            eMsg=u"%s"%e
            errorLines.append("%s\t--%s"%(line, eMsg))
            pass
    log=devlog(SN_id=device.SN, Cnt=okc, ECnt=len(errorLines), Object=dlogObj[:20], OpTime=datetime.datetime.now())
    try:
        log.save()
    except:
        try:
            device.save()
            log.save()
        except Exception,e:
            eMsg=u"%s"%e
            errorLines.append("%s\t--%s"%(line, eMsg))
            pass
    if errorLines:
        tmpFile("transaction_%s_%s.txt"%(device.SN, log.id), "\n".join(errorLines))
    return lc, okc

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
                except Exception,e:
                    appendFile(e + 'step 1')
                    continue

                if lines:
                    #lcc, okc=parseATransData(conn, cursor, lines.decode("utf-8").splitlines())
                    lcc, okc=parseATransData(conn, cursor, lines.splitlines())
                    lc+=lcc
                    i+=okc
                now=datetime.datetime.now()
                new_file="%s\\write\\%s\\%s"%(tmp_dir, now.strftime("%Y%m%d"), file_name)
                try:
                    #import shutil
                    #shutil.copy(tmp_file, new_file)
                    #os.remove(tmp_file)
                    os.renames(tmp_file, new_file)
                except:
                    try:
                        os.remove(tmp_file)
                    except Exception,e:
                         appendFile(e)
                fcount+=1
        if fcount==0:
            print "no transactions in the directory"
            time.sleep(10)
        
        if lc>50000: #太多记录，退出，下一次再继续
            break;
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

def performPostDataFile_(count=10):
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

def performPostDataFile(count=10):
    run_writedata(0)
