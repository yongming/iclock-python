from django.conf import settings
if settings.DATABASE_ENGINE=='pool':
    settings.DATABASE_ENGINE=settings.POOL_DATABASE_ENGINE

from django.core.management.base import BaseCommand, CommandError
import os
import time
import datetime
import sys

class Command(BaseCommand):
    option_list = BaseCommand.option_list + ()
    help = "Starts sync devices process."
    args = ''
 
    def handle(self, *args, **options):
        from mysite.iclock.syncdevice import sync_device 
        print self.help
        while True:
            sync_device(self)
            print datetime.datetime.now(),'sync devices over\n'
            time.sleep(60)
            

