from django.contrib import admin

# Register your models here.
from .models import Settings,Certificate
# Only superuser see this by default
admin.site.register(Certificate)
admin.site.register(Settings)
