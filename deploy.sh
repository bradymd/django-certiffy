git clone https://github.com/bradymd/django-certiffy.git
cd django-certiffy
python3 -m venv venv && source venv/bin/activate
cd django_certiffy_project
python3 -m pip install -r requirements.txt
python3 -m pip install --upgrade pip
rm db.sqlite3 
python manage.py migrate --fake-initial
python manage.py migrate --run-syncdb
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_PASSWORD=psw  python manage.py createsuperuser --email=admin@example.com --noinput
python manage.py runserver 
