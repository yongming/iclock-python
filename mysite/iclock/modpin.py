# -*- coding: utf-8 -*-
from mysite.iclock.models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from mysite.settings import PIN_WIDTH
from mysite.iclock.dataproc import appendDevCmd, devUpdateFirmware
from mysite.utils import *

#merge rmEmp's data to emp
def mergePIN(emp, rmEmp):
	#merge employee's name and department
	saveEmp=None
	ename=emp.EName
	if ename: 
		ename=ename.strip()
		if not ename and rmEmp.EName:
			ename=rmEmp.EName.strip()
			if ename:
				emp.EName=ename
				saveEmp=emp
	if (rmEmp.DeptID_id>1) and (emp.DeptID_id<=1):
		emp.DeptID=rmEmp.DeptID
		saveEmp=emp
	if saveEmp: saveEmp.save()

	for f in fptemp.objects.filter(UserID=rmEmp):
		f.UserID=emp
		try:
			f.save()
		except: pass
	for f in transaction.objects.filter(UserID=rmEmp):
		f.UserID=emp
		try:
			f.save()
		except: pass

def checkPINWidth():
	inv_emps=[]
	for emp in employee.objects.all():
		pin=formatPIN(emp.PIN)
		if emp.PIN<>pin: inv_emps.append(emp)
	for emp in inv_emps:
		pin=formatPIN(emp.PIN)
		emps=employee.objects.filter(PIN=pin)
		if emps.count()==0:
			print "modify PIN %s to %s"%(emp.PIN, pin)
			emp.PIN=pin
			emp.save()
		else:
			print "merge data PIN %s'%s' to %s'%s'"%(emp.PIN, emp.EName, pin, emps[0].EName)
			mergePIN(emps[0], emp)
			emp.delete()

