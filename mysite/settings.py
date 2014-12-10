#!/usr/bin/python
# -*- coding: utf-8 -*-
import os.path
import sys, time
# Django settings for mysite project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
WORK_PATH=os.path.split(__file__.decode(sys.getfilesystemencoding()))[0]
CACHE_BACKEND = 'file://%s/tmp/django_cache'%WORK_PATH
MANAGERS = ADMINS

DATETIME_FORMAT = 'Y-m-d H:i:s'
STD_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATABASE_ENGINE='sqlite3'
DATABASE_NAME=WORK_PATH+'/icdat.db'
#DATABASE_ENGINE = 'oracle'           #
#DATABASE_NAME = 'oracle9'             # 改成数据库名称
#DATABASE_USER = 'system'             # 改成数据库用户名.
#DATABASE_PASSWORD = 'admin'         # 改成数据库密码.
#DATABASE_HOST = '192.168.1.254'     # 改成数据库服务器地址
#DATABASE_PORT = '1521'             # 数据库服务器端口号,一般不用改

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Etc/GMT%+-d'%(time.timezone/3600)

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
LANGUAGE_CODE = 'zh-CN'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = WORK_PATH+'/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media'
ADDITION_FILE_ROOT = WORK_PATH+'/files/'
# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 't10g+$^b29eonku&fr+l50efir4&o==k*9)%#*zi5@osf6)q@x'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
	'mysite.iclocklocale.AuthenticationMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
	'mysite.iclocklocale.LocaleMiddleware',
#    'django.middleware.locale.LocaleMiddleware',
#    'django.middleware.cache.CacheMiddleware',
#    'django.middleware.doc.XViewMiddleware',
)

CACHE_MIDDLEWARE_SECONDS=25
_ = lambda s: s

LANGUAGES=(
  ('en', _('English')),
  ('zh-cn', _('Simplified Chinese')),
	('zh-tw', _('Tranditional Chinese')),
)

ROOT_URLCONF = 'mysite.urls'


TEMPLATE_DIRS = (
    WORK_PATH+'/templates',
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

#if 'mysite.iclocklocale.myContextProc' not in TEMPLATE_CONTEXT_PROCESSORS:
TEMPLATE_CONTEXT_PROCESSORS = (
	"django.core.context_processors.debug",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media",
    "django.core.context_processors.auth",
	'mysite.iclocklocale.auth',
	'mysite.iclocklocale.myContextProc',)

AUTHENTICATION_BACKENDS = (
	'django.contrib.auth.backends.ModelBackend',
	'mysite.authurls.EmployeeBackend',
	)



INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'mysite.iclock',
#    'rosetta',
#    'mysite.gallery',
)
#VERSION="Ver 2152(Build: 20081111)"
VERSION="v3.1-158"
ALL_TAG="ALL"

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
MAX_UPDATE_COUNT=0
UPDATE_COUNT=0
MCOUNT=0
APPEND_SLASH=False
LOGIN_REDIRECT_URL="/iclock/data/iclock/"
LOGIN_URL="/iclock/accounts/login/"
ICLOCK_AUTO_REG=1
PIN_WIDTH=1
transaction_absolute_path = ""
REBOOT_CHECKTIME=0  #
NOCMD_DEVICES=[]
ENCRYPT=0
PAGE_LIMIT=15
UPGRADE_FWVERSION="Ver 6.39 Jan  1 2009"
AUTO_PROXY_IP=""
MIN_TRANSINTERVAL=2 #最小传输数据间隔时间(分钟）
MIN_REQ_DELAY=60   #最小检查服务器命令间隔时间(秒）
DISABLED_PINS=[0]	#不允许的考勤号码
TRANS_REALTIME=1	#设备是否实时上传记录
DATABASE_USER='root'
DATABASE_PASSWORD=''
DATABASE_HOST='127.0.0.1'
DATABASE_PORT=1521
NATIVE_ENCODE='UTF-8'
MAX_EXPORT_COUNT=20000

SHORT_DATETIME_FMT='%y-%m-%d %H:%M:%S'
VSHORT_DATETIME_FMT='%y%m%d%H%M'
SHORT_DATETIME_FMT2='%m-%d %H:%M'
DATE_FMT='%y-%m-%d'
DATE_FMT4='%Y-%m-%d'
TIME_FMT='%H:%M:%S'

SHORT_DATETIME_FMT='%d/%m/%y %H:%M:%S'
VSHORT_DATETIME_FMT='%d/%m/%y%H%M'
SHORT_DATETIME_FMT2='%d/%m %H:%M'
DATE_FMT='%d/%m/%y'
DATE_FMT4='%d/%m/%Y'
TIME_FMT='%H:%M:%S'
##############################################
WRITE_DATA_CONNECTION=1
POOL_CONNECTION=5
WRITE_DATA_PORT=6380
SQL_POOL_PORT=3361

#############################################

from options import *


try:
	TMP_DIR=os.environ['TMP']
except:
	TMP_DIR="/tmp"

if not os.path.exists(TMP_DIR+"/"):
	TMP_DIR=os.path.split(os.tempnam())[0]

ENABLED_MOD=(
#	"msg", 		#信息定制模块
#	"weather", 	#天气预报模块
#	"udisk",	#导入U盘数据文件模块
#   "att",      #考勤管理模块
	)

UNIT=""

APP_HOME=os.path.split(WORK_PATH)[0]
LOG_DIR=APP_HOME+"\\tmp"

if "USER_COMPANY" in os.environ:
	UNIT=os.environ['USER_COMPANY']

if UNIT:
	UNIT_URL="/u/"+UNIT
	p_path=APP_HOME+'/attsite_'+UNIT+'.ini'
	LOGIN_REDIRECT_URL=UNIT_URL+"/iclock/data/iclock/"
	LOGIN_URL=UNIT_URL+"/iclock/accounts/login/"
	SESSION_COOKIE_PATH=UNIT_URL
	LOGOUT_URL=UNIT_URL+"/iclock/accounts/logout/"
elif len(sys.argv)>1 and not ("manage." in sys.argv[0]):
	UNIT_URL="/"
	p_path=APP_HOME+'/'+sys.argv[1]
else:
	UNIT_URL="/"
	p_path=APP_HOME+'/attsite.ini'

cfg=None
if os.path.exists(p_path):
	import dict4ini
	cfg=dict4ini.DictIni(p_path, 
		values={
		'DATABASE':{
			'ENGINE':DATABASE_ENGINE, 
			'NAME':DATABASE_NAME,
			'USER':DATABASE_USER, 
			'PASSWORD':DATABASE_PASSWORD, 
			'HOST':DATABASE_HOST, 
			'PORT':DATABASE_PORT, 
			},
		'SYS':{
			'PIN_WIDTH':PIN_WIDTH, 
			'ENCRYPT':ENCRYPT,
			'PAGE_LIMIT':PAGE_LIMIT, 
			'REALTIME':TRANS_REALTIME, 
			'AUTO_REG':ICLOCK_AUTO_REG,
			'NATIVE_ENCODE': NATIVE_ENCODE,
			'MAX_EXPORT_COUNT': MAX_EXPORT_COUNT,
			'TIME_ZONE': TIME_ZONE,
			'memcached': '', 
			'LOG_DIR':LOG_DIR,
			},
		'FTP':{
			'HOST':'10.1.1.254',
			'USER':'demo',
			'PASSWORD':'demo',
			'EMP_PATH':'/sap/emp',
			'SCH_PATH':'/sap/sch',
			'TRANS_PATH':'/sap/trans',
			'EMP_LOCAL':APP_HOME+'/tmp/processed/emp/',
			'SCH_LOCAL':APP_HOME+'/tmp/processed/sch/',
			},
		'LOCALE':{
			'SHORT_DATETIME_FMT'	:SHORT_DATETIME_FMT		,
			'VSHORT_DATETIME_FMT'	:VSHORT_DATETIME_FMT	,
			'SHORT_DATETIME_FMT2'	:SHORT_DATETIME_FMT2	,
			'DATE_FMT'				:DATE_FMT				,
			'DATE_FMT4'				:DATE_FMT4				,
			'TIME_FMT'				:TIME_FMT				,
			},
			})
	TIME_ZONE = cfg.SYS.TIME_ZONE
	DATABASE_NAME=cfg.DATABASE.NAME
	if DATABASE_NAME.startswith('{tmp_file}'):
		source=DATABASE_NAME[10:]
		target=TMP_DIR+"/"+source
		source=file(WORK_PATH+"/"+source,"rb").read()
		if not os.path.exists(target):
			f=file(target,"w+b")
			f.write(source)
			f.close()
		DATABASE_NAME=target
	DATABASE_ENGINE = cfg.DATABASE.ENGINE
	DATABASE_USER = cfg.DATABASE.USER
	DATABASE_PASSWORD = cfg.DATABASE.PASSWORD
	DATABASE_HOST = cfg.DATABASE.HOST
	DATABASE_PORT = cfg.DATABASE.PORT
	
	PIN_WIDTH=cfg.SYS.PIN_WIDTH
	ENCRYPT=cfg.SYS.ENCRYPT
	PAGE_LIMIT=cfg.SYS.PAGE_LIMIT
	TRANS_REALTIME=cfg.SYS.REALTIME 
	ICLOCK_AUTO_REG=cfg.SYS.AUTO_REG 
	NATIVE_ENCODE=cfg.SYS.NATIVE_ENCODE
	MAX_EXPORT_COUNT=cfg.SYS.MAX_EXPORT_COUNT
	if cfg.SYS.LOG_DIR=="{tmp_file}":
		LOG_DIR=TMP_DIR
		ADDITION_FILE_ROOT = TMP_DIR+'/files/'
	else:
		LOG_DIR=cfg.SYS.LOG_DIR
	if cfg.SYS.memcached:
		if "://" in cfg.SYS.memcached:
			CACHE_BACKEND = cfg.SYS.memcached
		else:
			CACHE_BACKEND="memcached://%s/"%cfg.SYS.memcached
	SHORT_DATETIME_FMT=cfg.LOCALE.SHORT_DATETIME_FMT
	VSHORT_DATETIME_FMT=cfg.LOCALE.VSHORT_DATETIME_FMT
	SHORT_DATETIME_FMT2=cfg.LOCALE.SHORT_DATETIME_FMT2
	DATE_FMT=cfg.LOCALE.DATE_FMT
	DATE_FMT4=cfg.LOCALE.DATE_FMT4
	TIME_FMT=cfg.LOCALE.TIME_FMT
MAX_DEVICES=100

#DEBUG=False

