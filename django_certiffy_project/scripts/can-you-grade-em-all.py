import getopt

import logging
logging.basicConfig(level=logging.WARN,format='%(process)-%(levelname)s-%(message)s')
logging.getLogger().setLevel(logging.WARN)
logging.captureWarnings(True)
logging.info('can-you-grade-em-all  program startup ')

# This trick allows this program to run standalone
import sys, os, django
sys.path.append("../..")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_certiffy_project.settings")
try:
        django.setup()
except:
        print('could not setup')

from certs.models import (Certificate,Settings)
from certs.modules.checkgrade import grade_ssllabs

helpmessage="""NAME:
  can-you-grade-em-all.py
SYNOPSIS:
  This has to irregularly to attempt to grade them all..
USAGE:
  source ~/.venv/certiffy/bin/activate
  can-you-grade-em-all.py  
AUTHOR: m.brady@herts.ac.uk"""

options=""
argv = sys.argv[1:]

try:
    options, args = getopt.getopt(argv, "h", [ "help"])
except:
    print("Check options")
    sys.exit()

for name, value in options:
    if name in ['-h', '--help']:
        print(helpmessage)
        sys.exit()
    else:
        print("No such option")
        sys.exit()


changes=[]

def recalculate(cert):
        madecontact, daysexpiry, expirydate = checkexpiry(
            cert.fqdn, cert.port, cert.expiry_date
        )
        global changes
        change={}
        if madecontact:
            if  cert.status == "DOWN":
                cert.status = "UP"
                change  = {'fqdn': cert.fqdn, 'status': 'UP'}
            if cert.daystogo == daysexpiry:
                pass
            if  cert.expiry_date != expirydate:
                cert.expiry_date = expirydate
                change  = {'fqdn': cert.fqdn, 'expiry_date': cert.expiry_date}
        if not madecontact:
            if cert.status == "UP":
                cert.status = "DOWN"
                change  = {'fqdn': cert.fqdn, 'status': 'DOWN' }
            if cert.daystogo != daysexpiry:
                cert.daystogo = daysexpiry
                change  = {'fqdn': cert.fqdn, 'daystogo': daysexpiry }
        if len(change) > 0:
                print(f'change happening {change}')
                changes.append(change)
                cert.save()

q=Certificate.objects.all()
cert_list = reversed(q.order_by("-daystogo"))
for cert in cert_list:
    if cert.grade == "N" and cert.status == "UP":
        print(f'{cert.fqdn},{cert.grade}...')
        status,cert.grade,message = grade_ssllabs(cert.fqdn)
        if status:
            cert.save()
        print(f'{cert.fqdn},{cert.grade}')

