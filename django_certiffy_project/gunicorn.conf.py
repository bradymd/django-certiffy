#[label gunicorn_config.py]
# this bind line has to match what you put in .env
bind = "localhost:8443"
workers = 4
# For Rocky/CentOS/RHEL
#certfile='/etc/pki/tls/certs/certiffy2023.ca-bundle'
#keyfile='/etc/pki/tls/private/certiffy2023.key'
# Ubuntu local certificates
#certfile="ssl/localhost.crt"
#keyfile="ssl/localhost.key"
loglevel = 'WARNING'
accesslog='/var/log/gunicorn/django-certiffy-access.log'
errorlog='/var/log/gunicorn/django-certiffy-error.log'
timeout = 240000
#check_config=True
reload=True
spew=False
reuse_port=True
cert_reqs = 1
proxy_allow_ips = '*'
# Put the output into error.log
capture_output=True
