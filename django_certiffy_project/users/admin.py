from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MyUser

fields = list(UserAdmin.fieldsets)
fields[0] = (None, {'fields': ('username', 'password', 'role')})
UserAdmin.fieldsets = tuple(fields)

admin.site.register(MyUser, UserAdmin)
