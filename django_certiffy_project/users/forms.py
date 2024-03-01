from django import forms
from django.db import models
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import MyUser

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=32,required=True)
    last_name = forms.CharField(max_length=32,required=True )
    role = models.CharField(max_length=10, blank=True)

    class Meta:
        model = MyUser
        fields = ["username", "role", "password1", "password2", "first_name", "last_name", "email"  ]

class UserUpdateForm(forms.ModelForm):
    username = models.CharField(max_length=30, unique=True)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=32,required=True)
    last_name = forms.CharField(max_length=32,required=True )
    role = models.CharField(max_length=10, blank=True)
    password = models.CharField(('password'), max_length=128, help_text=("Use '[algo]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>."))
    class Meta:
        model = MyUser
        fields = [ "username", "role", "password",  "first_name", "last_name", "email"  ]
    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['username'].disabled = True
        self.fields['email'].disabled = True

class MyPasswordChangeForm(PasswordChangeForm):
    pass

    class Meta:
        model = MyUser

class ResetPasswordForm(PasswordChangeForm):
    username = models.CharField(max_length=30, unique=True)
    password = models.CharField(('password'), max_length=128, help_text=("Use '[algo]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>."))
    class Meta:
        model = MyUser
        fields = [ "username", "password"   ]

class UploadFileForm(forms.Form):
    file=forms.FileField(label="")

#does this get used
class ExportFileForm(forms.Form):
    file=forms.CharField(max_length="512",label="Select")


