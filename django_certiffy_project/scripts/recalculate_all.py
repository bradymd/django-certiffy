import getopt

import logging
logging.basicConfig(level=logging.WARN,format='%(process)-%(levelname)s-%(message)s')
logging.getLogger().setLevel(logging.WARN)
logging.captureWarnings(True)
logging.info('mail-contacts.py program startup ')

# This trick allows this program to run standalone
import sys, os, django
sys.path.append("../.")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_certiffy_project.settings")
try:
        django.setup()
except:
        logging.debug('could not django.setup')

from certs.models import (Certificate,Settings)
from certs.modules.checkexpirym import checkexpiry
helpmessage="""NAME:
  recalculate-all.py
SYNOPSIS:
  This has to run regularly in the background, so a cron job.
USAGE:
  source ~/.venv/certiffy/bin/activate
  recalculate-all.py   [ -h | --run-from-commandline ]
AUTHOR: m.brady@herts.ac.uk"""

options=""
run_from_commandline=False
argv = sys.argv[1:]

try:
    options, args = getopt.getopt(argv, "hr", [ "help", "run-from-commandline"])
except:
    print("Check options")
    sys.exit()

for name, value in options:
    if name in ['-h', '--help']:
        print(helpmessage)
        sys.exit()
    elif name in [ '-r', '--run-from-commandline']:
        run_from_commandline=True
    else:
        print("No such option")
        sys.exit()


changes=[]

def recalculate(cert):
        madecontact, daysexpiry, expirydate = checkexpiry(
            cert.fqdn, cert.port, cert.expiry_date
        )
        global changes
        change=""
        #print(f'{cert.fqdn}:{cert.port} cert.daystogo={cert.daystogo}, daysexpiry={daysexpiry}')
        if madecontact:
            if  cert.status == "DOWN":
                cert.status = "UP"
                change  = f'{cert.fqdn}:{cert.port} changed cert.status={cert.status}'
            if cert.daystogo == daysexpiry:
                pass
            else:
                cert.daystogo = daysexpiry
                change  = f'{cert.fqdn}:{cert.port} changed daystogo={cert.daystogo}'
            if  cert.expiry_date != expirydate:
                cert.expiry_date = expirydate
                change  = f'{cert.fqdn}:{cert.port} changed expiry_date={cert.expiry_date}'
        if not madecontact:
            if cert.status == "UP":
                cert.status = "DOWN"
                change  = f'{cert.fqdn}:{cert.port} changed status={cert.status}'
                logging.debug(change)
            if cert.daystogo != daysexpiry:
                cert.daystogo = daysexpiry
                change  = f'{cert.fqdn}:{cert.port} changed daystogo={cert.daystogo}'
        if len(change) > 0:
                changes.append(change)
                cert.save()

def recalculate_all():
    logging.debug('recalculating all ...')
    cert_list = Certificate.objects.all()
    for cert in cert_list:
        recalculate(cert)
    for change in changes:
        logging.debug(f'{change}')

if run_from_commandline:
    recalculate_all()
    for change in changes:
        print( f'{change}')
