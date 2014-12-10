# -*- coding: utf-8 -*-

from django.core.management import execute_manager
try:
    from mysite import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
	import sys
	try:
		execute_manager(settings)
	except:
		pass
	if sys.argv[1]=="syncdb":
		from mysite.iclock.models import *
		print "create init data..."
		initDB()
