# Is called from certs:index when there is no settings  table (on installation)

import logging
logging.basicConfig(level=logging.WARN,format='%(process)-%(levelname)s-%(message)s')
logging.getLogger().setLevel(logging.DEBUG)


from django.contrib.contenttypes.models import ContentType
from certs.models import Certificate
from django.contrib.auth.models import AbstractUser, User, Group, Permission
from users.models import MyUser

def create_groups ():

  # This creates two groups (USER and ADMIN) and assigns permissions for the certificate object
  # User is created first so will have a key of 1, ADMIN will be 2
  logging.debug('This is create_groups ')
  for g in ["USER", "ADMIN"]:
    try:
      Group.objects.get(name=g)
      continue
    except:
      group = Group.objects.create(name=g)
    certificate_content_type = ContentType.objects.get_for_model(Certificate)
    certificate_permissions = Permission.objects.filter(
        content_type=certificate_content_type
    )
    for p in certificate_permissions:
        group.permissions.add(p)

  #  And now give additional permissions to the ADMIN group
  group = Group.objects.get(name="ADMIN")
  myuser_content_type = ContentType.objects.get_for_model(MyUser)
  myusers_permissions = Permission.objects.filter(content_type=myuser_content_type)
  for p in myusers_permissions:
    group.permissions.add(p)
