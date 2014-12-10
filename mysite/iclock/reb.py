import telnetlib
import threading
from mysite.utils import *
import time

def output(index,s):
	pass

okKey="ok"	

def DoInDev(ip, cmds):
	t=telnetlib.Telnet()
	t.open(ip)
	s=t.read_until("login:")
	output(1,s)						
	if s.find("on an MIPS")<0 or s.find("ZEM")<0:
		raise Exception("Not a valid host!\n")
	t.write("root\n")
	s=t.read_until("Password:")
	output(2,s)						
	t.write("sol"+okKey+"ey\n")
	s=t.read_until("\r\n#")
	output(3,s)
	ret=[]
	for cmd in cmds:
		t.write("%s\r\n"%cmd)
		s=t.read_until("\r\n#")
		ret.append(s)
		output(4,s)
	t.close()
	return ret

def tryDoInDev(ip, cmds):
	try:
		return DoInDev(ip, cmds)
	except Exception, e:
		return "ERROR: %s"%e

def rebootDev(ip):
	DoInDev(ip, ['reboot'])

def getFileDev(ip, file, tftpServerIp):
	DoInDev(ip, ["tftp -p -l %s -r %s_%s %s\r\n"%(file, file, ip, tftpServerIp)])

class telThread(threading.Thread):
	def __init__(self, ipList):
		threading.Thread.__init__(self)
		self.ips=ipList
	def run(self):
		for ip in self.ips:
			if ip:
				aip=ip
				if ip[-1]=='\n': aip=ip[:-1]
				try:
					rebootDev(aip)
					appendFile("%s: REBOOT %s OK"%(time.strftime("%y-%m-%d %H:%M:%S"),aip))
				except Exception, e:
					appendFile("%s: REBOOT %s FAIL: %s"%(time.strftime("%y-%m-%d %H:%M:%S"), aip, e))				

def rebDevsReal(iplist):
	for i in range(10000):
		ips=iplist[i*2:i*2+2]
		if ips:
			telThread(ips).start()
		else:
			break;

def rebDevs(iplist):
	return None
	rebDevsReal(iplist)

class DoCmdThread(threading.Thread):
	def __init__(self, ipList, Cmds):
		threading.Thread.__init__(self)
		self.ips=ipList
		self.cmds=Cmds
	def run(self):
		for ip in self.ips:
			if ip:
				aip=ip
				if ip[-1]=='\n': aip=ip[:-1]
				try:
					tryDoInDev(aip, self.cmds)
					print "%s: Run Cmds %s OK"%(time.strftime("%y-%m-%d %H:%M:%S"),aip)
				except Exception, e:
					print "%s: Run Cmds %s FAIL: %s"%(time.strftime("%y-%m-%d %H:%M:%S"), aip, e)

def DoCmdsByThread(iplist, cmds):
	for i in range(10000):
		ips=iplist[i:i+1]
		if ips:
			DoCmdThread(ips,cmds).start()
		else:
			break;

upgfw_cmds=["killall main wdt", "cd /mnt/mtdblock/", "tftp -g -r main_zem500_richard -l main 192.168.0.199","reboot"]
