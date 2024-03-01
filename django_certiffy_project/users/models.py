from django.db import models
from django.contrib.auth.models import AbstractUser


class MyUser(AbstractUser):
    ROLES = ( ( "ADMIN", "Admin"), ("USER", "User"))
    role= models.CharField(
           max_length=10, 
           choices=ROLES,
           default="USER", 
           blank=True
           )
