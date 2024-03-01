from django import forms
from .models import Certificate, Mail, Settings, Csr
from django.db import models
from multi_email_field.forms import MultiEmailField
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import InlineField
from crispy_forms.layout import Submit, Fieldset, Layout, MultiField, Div, HTML,Field
from django.conf import settings
import os

# If you change this, you probably want to import CertificateFormForImport
class CertificateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CertificateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'create-cert'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = False
        self.helper.form_asteriskField = False
        self.helper.form_action = 'certs:create'
        self.helper.add_input(Submit("submit", "Create"))
        self.fields['expiry_date'].disabled = True
        self.fields['status'].disabled = True
        self.fields['grade'].disabled = True
        self.fields['daystogo'].disabled = True
    class Meta:
        expiry_date = forms.CharField(max_length=256,disabled=True)
        model = Certificate
        fields = [
            "fqdn",
            "port",
            "daystogo",
            "contacts",
            "grade",
            "expiry_date",
            "status",
            "notes"
        ]
        widgets = { 
                    "fqdn" :forms.TextInput( 
                                 attrs={'size': 50}),
                    "contacts" : forms.Textarea(
                                attrs={'rows': 2}),
                    "notes" : forms.Textarea(
                                attrs={'rows': 4}),
                    } 
        constraints= [
                      models.UniqueConstraint(
                            fields=['fqdn','port'],
                            name='unique_fqdn_port')
                      ]

class MailForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MailForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'mailbyhand-form'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
                "to",
                "subject",
                InlineField('fromfield', readonly=True),
                "message_body"
                )
    class Meta:
        model = Mail
        fields = ["to","subject", "fromfield",  "message_body"]
        widgets={
                'message_body':forms.Textarea(attrs={'rows':10}),
                'fromfield':forms.TextInput(attrs={'readonly': 'readonly'})
                 }

class CsrForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CsrForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'mailbyhand-form'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
                "common_name",
                "country_name",
                "state_or_province_name",
                "organization_name",
                "organizational_unit_name",
                "locality_name",
                "subject_alternative_name",
                "email_address",
                )
    class Meta:
        model = Csr
        fields = ["common_name","country_name", "state_or_province_name",  "organization_name", "organizational_unit_name", "locality_name", "subject_alternative_name", "email_address" ]

class UploadFileForm(forms.Form):
    file=forms.FileField(label="")

#does this get used?
class ExportFileForm(forms.Form):
    file=forms.FileField(label="Select")

class SettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'settings'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = False
        self.helper.form_asteriskField = False
        self.helper.form_action = 'certs:settings'
        self.helper.add_input(Submit("submit", "Set"))
    class Meta:
        model = Settings
        fields = [
            "smtp",
            "default_from_field",
            "default_subject",
            "default_mail_template",
            "cron_mail",
            "Sun","Mon","Tue","Wed","Thu","Fri","Sat",
            "scheduled_hour",
            "daystogo_warning",
            "viewing_window",
        ]
        widgets = { 
                    "smtp" :forms.TextInput( 
                                 attrs={'size': 50}),
                    "default_mail_template" : forms.Textarea(
                                attrs={'rows': 10}),
                    } 

# This differs from CertificateForm in a marginal way:
#        self.fields['expiry_date'].disabled = False
#        self.fields['status'].disabled = False
#        self.fields['grade'].disabled = False
#        self.fields['daystogo'].disabled = False
# So that we can import a full export (backup?) including these fields
class CertificateFormForImport(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CertificateFormForImport, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'create-cert'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = False
        self.helper.form_asteriskField = False
        self.helper.form_action = 'certs:create'
        self.helper.add_input(Submit("submit", "Create"))
        self.fields['expiry_date'].disabled = False
        self.fields['status'].disabled = False
        self.fields['grade'].disabled = False
        self.fields['daystogo'].disabled = False

    class Meta:
        expiry_date = forms.CharField(max_length=256,disabled=True)
        model = Certificate
        fields = [
            "fqdn",
            "port",
            "daystogo",
            "contacts",
            "grade",
            "expiry_date",
            "status",
            "notes"
        ]
        widgets = { 
                    "fqdn" :forms.TextInput( 
                                 attrs={'size': 50}),
                    "contacts" : forms.Textarea(
                                attrs={'rows': 2}),
                    "notes" : forms.Textarea(
                                attrs={'rows': 4}),
                    } 
        constraints= [
                      models.UniqueConstraint(
                            fields=['fqdn','port'],
                            name='unique_fqdn_port')
                      ]

