
#coding=utf-8
from django.conf.urls.defaults import *
from django.contrib.auth.views import *
from django.contrib.auth import get_user, logout, REDIRECT_FIELD_NAME
import os
from mysite.iclock.models import adminLog, employee
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.core.cache import cache
from django.conf import settings

class EmployeeBackend(ModelBackend):
	def authenticate(self, username=None, password=None):
		try:
			u=User.objects.get(username='employee')
		except User.DoesNotExist:
			return None
		try:
			e=employee.objects.get(PIN=username)
		except ObjectDoesNotExist:
			return None
		pwd=e.Password
		if not pwd: pwd=username
		if pwd!=password:
			return None
		u.employee=e
		return u

def logon(request):
	ret=login(request)
	if not request.POST: return ret
	user=request.user
	if user.is_anonymous():
		return  render_to_response("info.html", {"title": _("Login"),
			"content": _("Invalid Username or Password, please try again.")});

	eb=-1
	try:
		eb=user.backend.find('EmployeeBackend')
	except: pass
	if eb==-1:
		user.employee=None
		if 'employee' in request.session:
			del request.session["employee"]
	else:
		request.session["employee"]=user.employee
	adminLog(User=user, action=u"LOGIN", object=request.META["REMOTE_ADDR"], model=u"%s"%user.employee).save()
	if user.is_staff: return ret
	logout(request)
	return render_to_response("info.html", {"title": _("Login"),
			"content": _("No permission to do anything!")});

@login_required
def logoff(request):
	user=get_user(request)
	logout(request)
	if 'employee' in request.session:
		del request.session["employee"]
	adminLog(User=user, action=u"LOGOUT", object=request.META["REMOTE_ADDR"]).save()
	return HttpResponseRedirect(settings.LOGIN_URL)

class PasswordChangeForm1(PasswordChangeForm):
	"A form that lets a user change his password."

	def isEmployeePwd(self):
		if 'employee' in self.request.session:
			e=self.request.session["employee"]
			pwd=e.Passwd or e.PIN
			if pwd==self.cleaned_data['new_password1']:
				return True
		return False

	def clean_old_password(self):
		# new_data, all_data
		"Validates that the old_password field is correct."
		if not self.isEmployeePwd():
			super(PasswordChangeForm1, self).clean_old_password()

	def save(self):
		"Saves the new password."
		if 'employee' in self.request.session:
			e=self.request.session["employee"]
			e.Passwd=self.cleaned_data['new_password1']
			e.save()
		else:
			super(PasswordChangeForm1, self).save()
			k="user_id_%s"%self.request.user.pk
			cache.delete(k)

@login_required
def password_change1(request, template_name='registration/password_change_form.html'):
	if request.POST:
		form = PasswordChangeForm1(request.user, request.POST)
		form.request=request
		if form.is_valid():
			form.save()
			return HttpResponseRedirect('%sdone/' % request.path)
	else:
		form = PasswordChangeForm1(request.user)
															 
	return render_to_response(template_name, {'form': form},
		context_instance=RequestContext(request))

urlpatterns = patterns('',
	('^logout/$', logoff),
	('^password_change/$', password_change1),
	('^password_change/done/$', password_change_done),
	('^login/$', logon),
	('^password_reset/$', password_reset),
	('^password_reset/done/$', password_reset_done),
	('^$', logon),

)

