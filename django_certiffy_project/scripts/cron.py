# This trick allows this program to run standalone
import sys, os, django, getopt
sys.path.append("../.")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_certiffy_project.settings")
try:
        django.setup()
except:
        logging.debug('could not django.setup')

from datetime import datetime
from certs.models import Settings
from scripts.smtplib_contacts import mail_contacts
from scripts.recalculate_all import recalculate_all

datetime_daysofweek = [ 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun' ]
crontab_daysofweek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'  ]
settings = Settings.objects.all().first()
scheduled_hours = [ settings.scheduled_hour ]
the_days_scheduled_cron_convention=[]
count=0
for day in [settings.Sun, settings.Mon, settings.Tue, settings.Wed, settings.Thu, settings.Fri, settings.Sat ]:
    if day:
        the_days_scheduled_cron_convention.append(count)
    count=count+1
# datetime_convention 0 is Monday
today_day = datetime_daysofweek [ datetime.today().weekday()  ]

def shall_we_email(the_days_scheduled_cron_convention, scheduled_hours):
    now_hour    =   datetime.now().hour
    now_minute  =   datetime.now().minute
    today_day = datetime_daysofweek [ datetime.today().weekday()  ]
    for day in the_days_scheduled_cron_convention:
        if crontab_daysofweek[day] == today_day:
            if int(now_hour) in scheduled_hours: 
                if ( now_minute  == 0  ):
                    return True
    return False

def cron():
    if shall_we_email(the_days_scheduled_cron_convention, scheduled_hours):
        recalculate_all()
        mail_contacts()

