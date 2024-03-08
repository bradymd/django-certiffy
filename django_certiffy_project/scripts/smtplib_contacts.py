import sys
import getopt
import re
from datetime import datetime, date,timedelta, timezone
from operator import itemgetter
import json

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import dns
import dns.resolver


import logging
logging.basicConfig(level=logging.WARN,format='%(process)-%(levelname)s-%(message)s')
logging.getLogger().setLevel(logging.WARN)

# This trick allows this program to run standalone
import sys, os, django
# we need this set to a variable ...
sys.path.append("../.")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_certiffy_project.settings")

try:
        django.setup()
except:
        logging.debug('could not setup django environment')

from certs.models import (Mail,Csr,Certificate,Settings)
from certs.forms import MailForm
from django.core.mail import send_mail
from certs.modules.dnslookup import dnslookup
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.template import Template , loader, Context

# This is not ideal, on install, no settings table
try:
    s=Settings.objects.all().first()
    MAIL_CONTACT_IF_LESS_THAN=int (s.daystogo_warning + 1 )
except:
    MAIL_CONTACT_IF_LESS_THAN=5

#This is just for development
mail=True

helpmessage="""NAME:
   mail-contacts.py
SYNOPSIS:
  Certificate Checker
  checks the number of daystogo and mails contact people, unless you run it with "--nomail" or "-q"
  It can be run from the command-line:
    mail-contacts.py --from-command-line
  Functions within  the program is trigged in the django program.
   
USAGE:
  source ~/.venv/certiffy/bin/activate
  mail-contacts.py [  [ --nomail ]  --from-command-line |  --help  
AUTHOR: m.brady@herts.ac.uk"""

options=""
from_command_line=False
argv = sys.argv[1:]

try:
    options, args = getopt.getopt(argv, "qhf", ["nomail", "help", "from-command-line"])
except:
    print("Check options")
    sys.exit()

for name, value in options:
    if name in ['-q', '--nomail']:
        mail  = False
    elif name in ['-h', '--help']:
        print(helpmessage)
        sys.exit()
    elif name in ['-f', '--from-command-line']:
        from_command_line=True
    else:
        print("No such option")
        sys.exit()


def mail_warning(contacts, fqdn, daystogo,expiry_date,port):
    if mail == False:
        logging.debug(f'didnt mail {contacts} about {fqdn},{port}')
        pass
    settings = Settings.objects.all().first()
    to = contacts
    fromfield = settings.default_from_field
    EMAIL_HOST = settings.smtp
    EMAIL_PORT = 25

    subject = settings.default_subject
    subject_template = Template(subject)
    # allow limited rendering in subject, we only send plain_subject
    context=Context(dict(   FQDN=fqdn,
                            PORT=port,
                            DAYSTOGO=daystogo,
                            EXPIRYDATE=expiry_date,
                            ))
    html_subject: str = subject_template.render ( context )
    plain_subject = strip_tags(html_subject)

    # this only comes back as html
    dnsmessage=dnslookup(fqdn,False)
    dnsmessage_template = Template(dnsmessage)
    context=Context(dict())
    html_dnsmessage: str = dnsmessage_template.render ( context )
    plain_dnsmessage = strip_tags(html_dnsmessage) 
    
    message_body  = settings.default_mail_template
    message_template=Template(message_body)
    context=Context(dict(
                            TO=to,
                            FROMFIELD=fromfield,
                            SUBJECT=subject,
                            FQDN=fqdn,
                            PORT=port,
                            DNSMESSAGE=html_dnsmessage,
                            DAYSTOGO=daystogo,
                            EXPIRYDATE=expiry_date,
                            ))

    html_message: str = message_template.render( context)
    plain_message = strip_tags(html_message)
    email={}
    # to has to be a string for the form
    email['to'] = ','.join(to)
    email['fromfield'] = fromfield
    email['subject'] = plain_subject
    email['message_body'] = html_message
    email['FQDN'] = fqdn
    email['port'] = port
    mailform = MailForm(email)
    if mailform.is_valid():
            try:
                smtp = smtplib.SMTP( EMAIL_HOST, EMAIL_PORT)
                smtp.ehlo()
                smtp.starttls()
                msg = MIMEMultipart('alternative')
                msg['Subject'] = plain_subject
                msg['To'] = email['to']
                msg.attach(MIMEText(plain_message,'plain'))
                msg.attach(MIMEText(html_message,'html'))
                smtp.sendmail(from_addr=fromfield,
                              to_addrs=to,
                              msg=msg.as_string())
                smtp.quit()
            except Exception as e:
                logging.debug(f'SMTP failure {e}')
    else:
        print('mailform is not valid')
        print(mailform.errors)

def mail_contacts():
    records = Certificate.objects.order_by("-daystogo")
    logging.debug(f'debug MAIL_CONTACT_IF_LESS_THAN = {MAIL_CONTACT_IF_LESS_THAN}')
    for website in records:
        if website.daystogo < MAIL_CONTACT_IF_LESS_THAN:
            logging.debug(f'mailing {website.contacts} about {website.fqdn}')
            mail_warning(website.contacts, website.fqdn, website.daystogo, website.expiry_date, website.port)

if from_command_line:
    mail_contacts()
