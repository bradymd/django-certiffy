from django.db import models
from django.utils import timezone
from multi_email_field.fields import MultiEmailField
from django_mysql.models import ListCharField
from django.db.models import  UniqueConstraint
import os
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator


# Create your models here.
class Certificate(models.Model):
    GRADE_CHOICES = (
        ("A+", "A+"),
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("F", "F"),
        ("N", "NONE"),
    )
    STATUS = (
        ("DOWN", "DOWN"),
        ("UP", "UP"),
        ("NK", "NOT KNOWN"),
    )
    fqdn = models.CharField(
        max_length=254,
        null=False,
        blank=False,
        help_text="(fully qualified name)",
        verbose_name="Host name:",
    )
    port = models.IntegerField(default=443)
    daystogo = models.IntegerField(
            default=0, 
            verbose_name="Days Before Expiry",
            help_text="(auto generated)",
            )
    contacts = ListCharField(
            max_length=254, 
            help_text="(comma separated email addresses)",
            base_field=models.EmailField(
                max_length=254,
                ),
    )
    grade = models.CharField(
        max_length=5,
        choices=GRADE_CHOICES,
        default="N",
        help_text="(auto generated)",
    )
    expiry_date = models.DateTimeField(
            default=timezone.now,
            help_text="(auto generated)",
            )
    status = models.CharField(
        max_length=9,
        choices=STATUS,
        default="NK",
        help_text="(auto generated)",
    )
    notes = models.TextField(
            editable=True,
            null=True,
            blank=True,
            help_text="Notes for you to manage this cert",
            )

    class Meta:
        unique_together = ('fqdn','port',)
        constraints= [ 
                      models.UniqueConstraint(
                            fields=['fqdn','port'],
                            name='unique_fqdn_port')
                      ]

    def __str__(self):
        return f"{self.fqdn},{self.port},{self.daystogo}"


class Mail(models.Model):
    to = ListCharField(
            max_length=254, 
            default="admin@example.com", 
            help_text="(comma separated email addresses)",
            base_field=models.EmailField(
                max_length=254,
                )
    )
    fromfield = models.EmailField(
        max_length=254,
        null=False,
        blank=False,
        default="admin@example.com",
        help_text="(Readonly. This is associated with your user record)",
        verbose_name="From:",
    )

    subject = models.CharField(
        max_length=254,
        null=False,
        blank=False,
        default="None",
        verbose_name="Subject:",
    )
    message_body = models.CharField(
            max_length=1024,
            blank=True,
            verbose_name="Message:",
            )

    def __str__(self):
        return f"{self.to}"

class Csr(models.Model):
    common_name = models.CharField(
            max_length=254, 
            blank=False,
            help_text="(fqdn eg example.com)",
            verbose_name="Common Name"
    )
    country_name = models.CharField(
        max_length=2,
        default='GB',
        blank=True,
        help_text="(eg GB)",
        verbose_name="Country Name:",
    )
    state_or_province_name = models.CharField(
        max_length=256,
        blank=True,
        verbose_name="State/Province/County:",
        help_text="(eg Hertfordshire)",
    )
    organization_name = models.CharField(
            max_length=256,
            blank=True,
            verbose_name="Organization:",
            help_text="(eg Company Name)"
            )
    organizational_unit_name = models.CharField(
            max_length=256,
            blank=True,
            verbose_name="Organizational Unit:",
            help_text="(eg Department Name)",
            )
    locality_name = models.CharField(
            max_length=256,
            blank=True,
            verbose_name="Locality:",
            help_text="(eg City)",
           )
    subject_alternative_name = ListCharField(
            max_length=256,
            verbose_name="Alternative Names:",
            blank=True,
            help_text="(eg example.com,www.example.com)",
            base_field=models.CharField(
                max_length=254,
                ),
            )
    email_address= models.EmailField(
            max_length=256,
            blank=True,
            verbose_name="Email Address:",
            help_text="(Recommended to leave blank)"
           )

    def __str__(self):
        return f"{self.to}"


class Settings(models.Model):
    smtp = models.CharField(
            max_length=254, 
            default="smtp.gmail.com",
            help_text="(smtp host)",
                )
    default_from_field = models.EmailField(
        max_length=254,
        null=False,
        blank=False,
        help_text="(Readonly. This is associated with your user record)",
        verbose_name="From:",
    )
    default_subject = models.CharField(
            max_length=254, 
            null=False,
            blank=False,
            default="({{DAYSTOGO}} days) {{FQDN}}:{{PORT}} Certificate Expiry",
            help_text="To reset to default use {{DEFAULT}}",
                )
    default_mail_template= models.TextField(
        max_length=512,
        blank=False,
        help_text="Use {{DEFAULT}} to reset. You can use: https://{{FQDN}}:{{PORT}},{{DAYSTOGO}},{{DNSMESSAGE}},{{EXPIRYDATE}}'",
        default="""
        This is an automated message:<br>
        <ul>
        <li>https://{{FQDN}}:{{PORT}} expires in {{DAYSTOGO}} days</li>
        <li>Expiry Date : {{EXPIRYDATE}}</li>
        </ul>
        You are the listed contact for facilitating the renewal of this certificate.<br>
        Thank-you</p>

        -----------<br>
        {{DNSMESSAGE}}
        """,
        verbose_name="Default Mail Template:",
    )
    cron_mail = models.BooleanField(
            default=False,
            )
    Sun = models.BooleanField(default=False,help_text="Sun")
    Mon = models.BooleanField(default=True,help_text="Mon")
    Tue = models.BooleanField(default=True,help_text="Tue")
    Wed = models.BooleanField(default=True,help_text="Wed")
    Thu = models.BooleanField(default=True,help_text="Thu")
    Fri = models.BooleanField(default=True,help_text="Fri")
    Sat = models.BooleanField(default=False,help_text="Sat")
    scheduled_hour = models.IntegerField( default=8, 
                                         validators=[MaxValueValidator(23), MinValueValidator(0)],
                                         help_text="(Hour to Send cron Mail)",
                                         )

    daystogo_warning = models.IntegerField(default=8,
            help_text="(Days before expiry from when action is expected (suggest 8))",
                                           )
    viewing_window  = models.IntegerField(default=14,
            help_text="(How many days displayed in the graph view (recommend 14))",
                                           )

    def __str__(self):
        return f"{self.smtp}"

"""
class Document(models.Model):
    docfile = models.FileField(upload_to='uploads')
    def __str__(self):
        return f"{self.docfile}"
    def __unicode__(self):
        return '%s' % (self.docfile.name)
    def delete(self, *args, **kwargs):
        print(dir(self))
        os.remove(os.path.join(settings.MEDIA_ROOT, self.docfile.name))
        super(Document,self).delete(*args,**kwargs)
        documents = Document.objects.all()
        for document in documents:
            document.delete()

    def tidy(self, *args, **kwargs):
        os.remove(os.path.join(settings.BASE_DIR,"uploads", self.docfile.name))

        super(Document,self).delete(*args,**kwargs)
        documents = Document.objects.all()
        for document in documents:
            document.delete()
"""
