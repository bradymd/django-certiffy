## QUICK START FOR TRYING OUT
```
sh deploy.sh
```

Take a look ![Screenshots](screenshots.md)


## BUILD FOR PRODUCTION THOUGHTFULLY
```
cd /var/www
mkdir django-certiffy
chown certiffy:certiffy django-certiffy
su  certiffy
git clone https://github.com/bradymd/django-certiffy.git
```

## INSTALL THE PYTHON ENVIRONMENT
```
cd django-certiffy
python3 -m venv venv && source venv/bin/activate
cd django_certiffy_project
python3 -m pip install -r requirements.txt
python3 -m pip install --upgrade pip
```

## NO DB NEEDED ON INSTALL
Empty file or remove it.
```
rm db.sqlite3 
```

## CONFIGURE THE DATABASE
```
python manage.py migrate --fake-initial
python manage.py migrate --run-syncdb
```


## CREATE THE ADMIN USER
```
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_PASSWORD=psw  python manage.py createsuperuser --email=admin@example.com --noinput
```

BUG: The first user"admin"  is put as Group "USER".\
WORKAROUND: use the tab django-admin to change the Role to "ADMIN"


## TEST RUN IN DEBUG MODE
```
python manage.py runserver :8443
```
After login it should go to the "settings" page  to create the settings table, check the form and "update settings".

## LOCAL FIREWALL READY FOR PRODUCTION
```
firewall-cmd --add-rich-rule='rule family="ipv4" port port="8443" protocol="tcp" accept' --permanent
firewall-cmd --reload
```

## CONFIGURE ACCESS TO LOCALHOST
```
HOSTNAME="$(hostname)"
sed -e 's/ALLOWED_HOSTS.*/ALLOWED_HOSTS = [ "'$HOSTNAME'" ]/' -i django_certiffy_project/django_certiffy_project/settings.py
```

# ODD THING ABOUT GROUPS
The Groups '[ "ADMIN", "USER" ] get put in when users in those groups are CREATED.
This doesn't apply if you create a User and then UPDATE it to have the second group.

## RUN GUNICORN TO RUN IN PRODUCTION
```
pip install gunicorn
#cd django_certiffy_project/
# test:
#	gunicorn django_certiffy_project.wsgi
# configure for certs:
#vi ../gunicorn.conf.py
```
## CONFIGURE TO START FOR PRODUCTIOIN
```
#install -d /etc/systemd/system django-certiffy.service
#systemctl enable django-certiffy.service --now
```

## DJANGO SYSTEMD SERVICE
```
[Unit]
Description=Gunicorn instance to serve django-certiffy
After=network.target

[Service]
User=certiffy
Group=certiffy
WorkingDirectory=/var/www/django-certiffy/django_certiffy_project
Environment="PATH=/var/www/django-certiffy/venv/bin"
#ExecStart=/var/www/django-certiffy/venv/bin/gunicorn --workers 3 -m 007 django_certiffy_project.wsgi
ExecStart=/var/www/django-certiffy/venv/bin/gunicorn django_certiffy_project.wsgi

[Install]
WantedBy=multi-user.target
```

## CONFIGURE APACHE TO PROXY TO GUNICORN
/etc/apache/conf.d/ssl.conf:
```
<VirtualHost *:443>
ServerName certiffy.herts.ac.uk
SSLproxyEngine On
Timeout 600
<Directory /var/www/django-certiffy/django_certiffy_project/static>
    Order allow,deny
    Options Indexes
    Allow from all
</Directory>
Alias /static/ /var/www/django-certiffy/django_certiffy_project/static/
Alias /static/admin/ /var/www/django-certiffy/django_certiffy_project/static/admin/
ProxyPass /static/ !
ProxyPass / http://localhost:8443/
ProxyPassReverse / "http://localhost:8443/"
ErrorLog logs/django-certiffy-error.log
TransferLog logs/django-certiffy-access.log
LogLevel warn
SSLEngine on
SSLHonorCipherOrder on
SSLCipherSuite PROFILE=SYSTEM
SSLProxyCipherSuite PROFILE=SYSTEM
SSLCertificateFile /etc/pki/tls/certs/certiffy2023.ca-bundle
SSLCertificateKeyFile /etc/pki/tls/private/certiffy2023.key
</VirtualHost>
```

# TO FACILIATE MAILING CONTACTS AND AUTO CHECKING, SET UP CRON
Run crontab add twice:
```
python manage.py crontab add
python manage.py crontab add
python manage.py crontab show
```


# FOREIGN KEY contraint - ISSUE IMPORTING USERS
The export of the users table to a json file will have an integer representing the group \"USER\" and \"ADMIN\".  
On a new install these will be  \"1\" and \"2\".   
On   some older certiffy systems I\'ve seen \"8\" and \"9\".   
Anyway, this can stop it being imported and you can get the error \'FOREIGN KEY constraint failed\'.   
You can use vim to:
```
s/\[8]/\[1]/g  
s/\[9]/\[2]/g  
```
You can import on the command line:
```
python manage.py loaddata imported.json
```


