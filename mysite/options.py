# -*- coding: utf-8 -*-
CACHE_BACKEND = 'memcached://127.0.0.1:11211;127.0.0.1:11212;127.0.0.1:11213/?max_entries=40000'      # 使用缓存MIN_TransInterval = 10    
CMD_QUEQE=True	#ÊÇ·ñÊ¹ÓÃÉè±¸ÃüÁî»º´æ¶ÓÁÐ£¬²»Ê¹ÓÃÊ±£¬ÆäÖ±½Ó´ÓÊý¾Ý¿âÖÐ¶ÁÈ¡ÃüÁî
#TIME_ZONE = 'Etc/GMT+8'



# -*- coding: utf-8 -*-

#POOL_DATABASE_ENGINE = 'oracle'                    # 真实的数据库引擎 
#DATABASE_ENGINE = 'pool'                           # 使用连接池引擎 
#DATABASE_NAME = 'sales'                            # 改成数据库名称
#DATABASE_USER = 'afcssynopr'                       # 改成数据库用户名.
#DATABASE_PASSWORD = 'afcs1234'                     # 改成数据库密码.
#DATABASE_HOST = 'sales.db.paic.com.cn'             # 改成数据库服务器地址 '10.33.30.199'
#DATABASE_PORT = '1534'                             # 数据库服务器端口号,一般不用改

# -*- coding: utf-8 -*-
DATABASE_USER = 'root'                       # 改成数据库用户名.
DATABASE_PASSWORD = ''                     # 改成数据库密码.
DATABASE_PORT = '83306'                             # 数据库服务器端口号,一般不用改
DATABASE_ENGINE = 'mysql'                           #使用连接池引擎
POOL_DATABASE_ENGINE = 'mysql'                         # 测试用
DATABASE_NAME = "adms_db"
DATABASE_HOST = '127.0.0.1'             # 改成数据库服务器地址 '10.33.30.199'

ICLOCK_AUTO_REG = 1		                   # 允许连接的设备自动注册
PIN_WIDTH = 10			                   # 考勤号码宽度
#AUTO_PROXY_IP="10.12.102.81"                       # 自动代理服务器ip
MIN_TransInterval = 10                             # 连接间隔，单位：分
MIN_REQ_DELAY = 30                                # 最小请求间隔，单位：秒
UPGRADE_FWVERSION = "Ver 5.36 May 27 2010"         # 升级固件
UPLOAD_TIMES="06:00;12:00;16:00;19:00;20:00;21:00;22:00;23:00"
INTERNAL_IPS=("127.0.0.1",)

DevEmployees_Updated_Day = 7





