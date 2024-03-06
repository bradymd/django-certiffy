from django.shortcuts import ( render,
    get_object_or_404,
    HttpResponseRedirect,
)
from django.contrib import messages
from django.http import HttpResponse
from .models import Certificate,Settings
from users.models import MyUser
from .forms import (
    CertificateForm,
    MailForm,
    UploadFileForm,
    ExportFileForm,
    CertificateFormForImport,
    SettingsForm,
    CsrForm
)
from django.urls import reverse
from .modules import checkexpirym, checkgrade, readcert, gencertsr
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Permission
import pytz
from django.conf import settings as settings_py
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.html import strip_tags
from django.template import Template, Context
import re, os, csv
from .modules.filehandler import handle_uploaded_file
from .modules.download_csv import download_csv
from .modules.dnslookup import dnslookup
from django.db import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import ExtensionOID
import scripts.recalculate_all
import smtplib,ssl
from scripts.smtplib_contacts import mail_contacts
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import logging
logging.basicConfig(level=logging.WARN,format='%(process)-%(levelname)s-%(message)s')

# Create your views here.
@login_required
@permission_required("certs.view_certificate")
def index(request):
    q=Certificate.objects.all()
    s=Settings.objects.all().first()
    if s == None:
        return HttpResponseRedirect(reverse("certs:settings"))
    queryset = reversed(q.order_by("-daystogo"))
    context = {
        "cert_list": queryset,
        "user": request.user,
        "role": request.user.get_role_display(),
        "count": len(q),
        "daystogo_warning": s.daystogo_warning,
    }
    return render(request, "certs/index.html", context)


@login_required
@permission_required("certs.view_certificate")
def search(request):
    query = request.GET.get("fqdn")
    print(f"fqdn={query}")
    queryset = reversed(
        Certificate.objects.filter(fqdn__icontains=query).order_by("-daystogo")
    )
    s=Settings.objects.all().first()
    context = {
        "cert_list": queryset,
        "user": request.user,
        "role": request.user.get_role_display(),
        "count": len(query),
        "daystogo_warning": s.daystogo_warning,
    }
    return render(request, "certs/index.html", context)


@login_required
@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.delete_certificate")
@permission_required("certs.change_certificate")
def create(request):
    if request.method == "POST":
        form = CertificateForm(request.POST)
        if form.is_valid():
            try:
                form.save()
            except:
                messages.add_message(
                    request,
                    messages.ERROR,
                    f"Record {form.cleaned_data['fqdn']}:{form.cleaned_data['port']} failed to add!",
                )
            messages.add_message(
                request,
                messages.SUCCESS,
                f"Record {form.cleaned_data['fqdn']}:{form.cleaned_data['port']} added successfully!",
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                f"Now Check Expiry and Status for the first time!",
            )
            obj = get_object_or_404(
                Certificate,
                fqdn=form.cleaned_data["fqdn"],
                port=form.cleaned_data["port"],
            )
            return HttpResponseRedirect(reverse("certs:detail", kwargs={"id": obj.id}))
        else:
            if "already exists" in str(form.errors):
                message = mark_safe(f"Record failed to add!<br>its a duplicate")
            else:
                message = mark_safe(f"Record failed to add!<br>{form.errors}")
            messages.add_message(request, messages.WARNING, message)
            context = {"form": CertificateForm(request.POST)}
            return render(request, "certs/create.html", context)
    else:
        context = { "form": CertificateForm() }
        return render(request, "certs/create.html", context)


@login_required
@permission_required("certs.view_certificate")
def detail(request, id):
    obj = get_object_or_404(Certificate, id=id)
    form = CertificateForm(request.POST or None, instance=obj)
    context = {
        "form": form,
        "id": id,
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    return render(request, "certs/detail.html", context)


@login_required
@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.change_certificate")
def update(request, id):
    obj = get_object_or_404(Certificate, id=id)
    # without instance=obj below, it will write a new instance
    form = CertificateForm(request.POST or None, instance=obj)
    contacts = request.POST.get("contacts")
    if request.method == "POST":
        fqdn = request.POST.get("fqdn")
        port = request.POST.get("port")
        if form.is_valid():
            try:
                # Certificate.objects.get(id=id).delete()
                form.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Record {form.cleaned_data['fqdn']}:{form.cleaned_data['port']} updated!",
                )
            except:
                messages.add_message(
                    request, messages.ERROR, f"Record {fqdn}:{port} failed to update!"
                )
            return render(
                request, "certs/update.html", context={"id": id, "form": form}
            )
        else:
            logging.debug("Form is not valid then ... ")
            logging.debug(f"Contacts is {contacts}")
            logging.debug(type(contacts))
            logging.warning(form.errors)
            messages.add_message(
                request,
                messages.WARNING,
                f"Record {fqdn}:{port} DID NOT UPDATE!",
            )
            logging.debug("problem with the form")
            return render(
                request, "certs/update.html", context={"id": id, "form": form}
            )
    else:
        # First click on Edit - there is no POST?
        context = {
            "id": id,
            "form": CertificateForm(instance=obj),
            "user": request.user,
            "role": request.user.get_role_display(),
        }
        return render(request, "certs/update.html", context)


@login_required
@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.delete_certificate")
@permission_required("certs.change_certificate")
def delete(request, id):
    obj = get_object_or_404(Certificate, id=id)
    record = Certificate.objects.get(id=id)
    try:
        Certificate.objects.get(id=id).delete()
    except:
        messages.add_message(
            request, messages.ALERT, f"Record {record.fqdn} failed to delete!"
        )
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Record {record.fqdn}:{record.port} deleted successfully!",
    )
    return HttpResponseRedirect(reverse("certs:index"))


@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.delete_certificate")
@permission_required("certs.change_certificate")
@login_required
def checkexpiry(request, id):
    obj = get_object_or_404(Certificate, id=id)
    record = Certificate.objects.get(id=id)
    logging.debug("checkexpiry_view:")
    if request.method == "POST" or "GET":
        madecontact, daysexpiry, expirydate = checkexpirym.checkexpiry(
            record.fqdn, record.port, record.expiry_date
        )
        logging.debug(
                f"{record.fqdn}:{record.port} madecontact= {madecontact}, daysexpiry = {daysexpiry}, expirydate = { expirydate }, record.expiry_date - {record.expiry_date})"
        )
        if madecontact:
            if record.daystogo == daysexpiry:
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Still {daysexpiry} days to go !",
                )
            else:
                record.daystogo = daysexpiry
            if record.expiry_date != expirydate:
                # changing expiry date
                tmp_expiry_date = record.expiry_date
                record.expiry_date = expirydate
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Updated Expiry Date from {tmp_expiry_date}",
                )
            record.status = "UP"
            record.save()
            # messages.add_message(
            #    request,
            #    messages.SUCCESS,
            #    f"Record {record.fqdn}:{record.port} {record.daystogo} to go!",
            # )
        else:
            # Not Valid means host could not be checked, so status DOWN
            record.status = "DOWN"
            record.daystogo = daysexpiry
            record.save()
            messages.add_message(
                request,
                messages.WARNING,
                mark_safe(
                    f"Host {record.fqdn}:{record.port} is down<br>{record.daystogo} days to go!"
                ),
            )
    obj = get_object_or_404(Certificate, id=id)
    context = {"form": CertificateForm(instance=obj), "id": id}
    return render(request, "certs/detail.html", context)

@login_required
@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.delete_certificate")
@permission_required("certs.change_certificate")
def grade(request, id):
    obj = get_object_or_404(Certificate, id=id)
    record = Certificate.objects.get(id=id)
    logging.debug("grade_view:")
    if request.method == "POST" or "GET":
        isvalid, grade, message  = checkgrade.grade_ssllabs(record.fqdn)
        logging.debug(f"isvalid={isvalid}, grade= {grade}, message={message})")
        if isvalid:
            if record.grade == grade:
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Grade {grade}  !",
                )
            elif record.grade != grade:
                tmp_grade = record.grade
                record.grade = grade
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Grade updated from {tmp_grade} to {grade}",
                )
            record.status = "UP"
            record.save()
        else:
            # Not Valid means host could not be checked
            # Could be many reasons so dont assume connection/dns was fine
            #record.grade = "N"
            #record.save()
            messages.add_message(
                request,
                messages.WARNING,
                f"Host could not be graded by ssllabs leaving as {record.grade}! {message}",
            )
    obj = get_object_or_404(Certificate, id=id)
    context = {"form": CertificateForm(instance=obj), "id": id}
    return render(request, "certs/detail.html", context)

@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.delete_certificate")
@permission_required("certs.change_certificate")
@login_required
def recalculate_all(request):
    # this has to run from cron as well as here , so I call the cron code
    s = scripts.recalculate_all
    s.recalculate_all()
    return HttpResponseRedirect(reverse('certs:index'))


@login_required
def mail(request, id):
    if request.method == "POST":
        # populate the form
        mailform = MailForm(request.POST)
        if mailform.is_valid():
            # the fromfield doesn't come back from the form
            # as its readonly
            # but we want it from the logged in user anyway
            fromfield = str(request.user.email)
            settings = Settings.objects.all().first()
            EMAIL_HOST = settings.smtp
            EMAIL_PORT = 25
            plain_subject = mailform.cleaned_data["subject"]
            plain_message : str = strip_tags(mailform.cleaned_data["message_body"])
            html_message=mailform.cleaned_data["message_body"]
            to=",".join(mailform.cleaned_data["to"])
            try:
                smtp = smtplib.SMTP( EMAIL_HOST, EMAIL_PORT)
                smtp.ehlo()
                smtp.starttls()
                msg = MIMEMultipart('alternative')
                msg['Subject'] = plain_subject
                msg['From'] = fromfield
                msg['To' ] = to
                msg.add_header('Content-Type', 'text')
                msg.attach(MIMEText(plain_message,'plain'))
                msg.attach(MIMEText(html_message,'html'))
                smtp.sendmail( fromfield,
                              to,
                              msg=msg.as_string() )
                smtp.quit()
            except Exception as e:
                logging.debug(f'SMTP failure {e}')
                messages.add_message(
                    request,
                    messages.WARNING,
                    mark_safe(
                        f'Could not mail {mailform.cleaned_data["to"]} about {mailform.cleaned_data["subject"]} from {fromfield} <br>e.args[1], check connection to {EMAIL_HOST}'
                    ),
                )
                context = {
                    "id": id,
                    "user": request.user,
                    "role": request.user.get_role_display(),
                }
                return HttpResponseRedirect(reverse("certs:detail", kwargs={"id": id}))
            messages.add_message(
                request,
                messages.SUCCESS,
                f"Mailed!",
            )
            # something badly wrong so back to certs:index
            return HttpResponseRedirect(reverse("certs:index"))
        else:
            messages.add_message(
                request,
                messages.WARNING,
                f"Form not valid!",
            )
            context = {
                "id": id,
                "form": mailform,
                "user": request.user,
                "role": request.user.get_role_display(),
            }
            return render(request, "certs/mail.html", context)
    else:
        # This is the GET request
        record = Certificate.objects.get(id=id)
        me = MyUser.objects.get(username=request.user)
        
        settings = Settings.objects.all().first()
        # turn the contacts field (comma separated) into list
        to = ",".join(record.contacts)
        fromfield = me.email

        subject = settings.default_subject
        subject_template = Template(subject)
        context=Context(dict(   FQDN=record.fqdn,
                                PORT=record.port,
                                DAYSTOGO=record.daystogo,
                                EXPIRYDATE=record.expiry_date,))
        html_subject: str = subject_template.render ( context )
        plain_subject = strip_tags(html_subject)

        html_dnsmessage=dnslookup(record.fqdn,False)
        
        message_body = settings.default_mail_template
        message_template = Template ( message_body )
        context=Context(dict(
                            TO=to,
                            FROMFIELD=fromfield,
                            SUBJECT=plain_subject,
                            FQDN=record.fqdn,
                            PORT=record.port,
                            DNSMESSAGE=html_dnsmessage,
                            DAYSTOGO=record.daystogo,
                            EXPIRYDATE=record.expiry_date,
                            ))
        html_message: str = message_template.render ( context )

        data = {
            "to": to,
            "subject": plain_subject,
            "message_body": html_message,
            "fromfield": fromfield,
        }
        # populate the form
        mailform = MailForm(data)
        context = {
            "id": id,
            "form": mailform,
            "user": request.user,
            "role": request.user.get_role_display(),
            "notes": record.notes,
        }
        return render(request, "certs/mail.html", context)


@login_required
@csrf_exempt
@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.delete_certificate")
@permission_required("certs.change_certificate")
def importcsv(request):
    context = {
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # upload the a file and leave it in imported.csv
            handle_uploaded_file(request.FILES["file"])
            reader = csv.reader(open("imported.csv"))
            # now validate each line using CertificateForm
            for row in reader:
                message = ""
                if len(row) == 0:
                    continue
                if len(row) != 3 and len(row) != 8:
                    message = (
                        message
                        + f"{len(row)} fields  should be 3 or 8<br>: {row[0]}..."
                    )
                    messages.add_message(request, messages.WARNING, mark_safe(message))
                    continue
                if len(row) == 3:
                    fqdn, port, contacts = row
                    formparams = {
                        "fqdn": fqdn,
                        "port": port,
                        "contacts": contacts,
                        "daystogo": 0,
                        "grade": "N",
                        "status": "NK",
                    }
                if len(row) == 8:
                    fqdn, port, daystogo, contacts, grade, expiry_date, status, notes = row
                    formparams = {
                        "fqdn": fqdn,
                        "port": port,
                        "daystogo": daystogo,
                        "contacts": contacts,
                        "grade": grade,
                        "expiry_date": expiry_date,
                        "status": status,
                        "notes": notes
                    }
                f = CertificateFormForImport(formparams)
                try:
                    f.is_valid()
                    f.save()
                except IntegrityError as e:
                    # this isnt working, though the unique constraint is being enforced  from the model
                    if "unique constraint".lower() in str(e.args).lower():
                        message = str(e.args[0]) + "Duplicate error"
                except Exception as e:
                    # a second way to see if we have a duplicate
                    if port.isdigit():
                        if Certificate.objects.filter(
                            fqdn__iexact=fqdn, port__iexact=port
                        ):
                            message = (
                                message
                                + str(e.args[0])
                                + f"<br><b>{fqdn}:{port} Duplicate error</b><br>"
                            )
                            messages.add_message(
                                request, messages.WARNING, mark_safe(message)
                            )
                            continue
                    else:
                        message = (
                            message
                            + f"Could not import {fqdn},{port},{contacts}, {port} <b>is not a digit</b><br>"
                        )
                        messages.add_message(
                            request, messages.WARNING, mark_safe(message)
                        )
                        continue
                    message = message + f"Could not import {fqdn},{port},{contacts}<br>"
                    for field in f:
                        for error in field.errors:
                            message = message + f"<br><b>{field.label}:</b> {error}"
                    messages.add_message(request, messages.WARNING, mark_safe(message))
            return HttpResponseRedirect(reverse("certs:index"))
        else:
            message = "Failed to get that file"
            messages.add_message(request, messages.WARNING, mark_safe(message))
    else:
        form = UploadFileForm()
    context.update({"form": form})
    return render(request, "certs/import.html", context)


@login_required
@csrf_exempt
@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.delete_certificate")
@permission_required("certs.change_certificate")
def exportcsv(request):
    if request.POST:
        form = ExportFileForm(request.POST, request.FILES)
        data = download_csv(Certificate, request, Certificate.objects.all())
        response = HttpResponse(data, content_type="text/csv;charset=utf-8")
        filename = request.POST.get("file")
        response["Content-Disposition"] = "attachment; filename=" + filename
        return response
    else:
        form = ExportFileForm()
        context = {
            "user": request.user,
            "role": request.user.get_role_display(),
        }
        context.update({"form": form})
        return render(request, "certs/export.html", context)


@login_required
@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.delete_certificate")
@permission_required("certs.change_certificate")
def deleteall(request):
    context = {
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    if request.POST:
        Certificate.objects.all().delete()
        return HttpResponseRedirect(reverse("certs:index"))
    return render(request, "certs/deleteall.html", context)

@login_required
@csrf_exempt
@permission_required("certs.view_certificate")
@permission_required("certs.add_certificate")
@permission_required("certs.delete_certificate")
@permission_required("certs.change_certificate")
def settings(request):
    # this table has just one record, I use .first()
    obj=Settings.objects.all().first()
    if  request.method == "POST" and obj:
        form = SettingsForm(request.POST or None, instance=obj)
    elif request.method == "POST" and  obj == None  :
        form = SettingsForm(request.POST)
    elif  request.method == "GET" and obj  :
        form = SettingsForm(instance=obj)
    elif request.method == "GET":
        # this would be the first time, no data
        form = SettingsForm()
    context = {
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    if request.POST:
        if form.is_valid():
            if form.cleaned_data['default_mail_template']  == '{{DEFAULT}}':
                setattr(obj, 'default_mail_template', obj._meta.fields[4].default )
            if form.cleaned_data['default_subject']  == '{{DEFAULT}}':
                setattr(obj, 'default_subject', obj._meta.fields[3].default )
            form.save()
            message = "Settings Updated"
            messages.add_message(request, messages.SUCCESS, mark_safe(message))
        else:
            logging.debug('form is not valid')
            message = "Form isn't valid"
            messages.add_message(request, messages.WARNING, mark_safe(message))
        return HttpResponseRedirect(reverse("certs:index"))
    else:
        cronjobs=settings_py.CRONJOBS
        context.update( { 'form': form })
        context.update( { 'cronjobs': cronjobs } )
    return render(request, "certs/settings.html", context)

@login_required
def gencsr(request, id):
    record = Certificate.objects.get(id=id)
    if request.method == "POST":
        # populate the form
        csrform = CsrForm(request.POST)
        if csrform.is_valid():
           context={}
           context['common_name']=csrform.cleaned_data['common_name']
           context['country_name']=csrform.cleaned_data['country_name']
           context['state_or_province_name']=csrform.cleaned_data['state_or_province_name']
           context['locality_name']=csrform.cleaned_data['locality_name']
           context['organization_name']=csrform.cleaned_data['organization_name']
           context['organizational_unit_name']=csrform.cleaned_data['organizational_unit_name']
           context['email_address']=csrform.cleaned_data['email_address']
           context['subject_alternative_name']=csrform.cleaned_data['subject_alternative_name']
           pemcsr,pemkey,csrobj=gencertsr.gencertsr(context)

           # Really we should read the csr to show what is in it
           #csr = x509.load_pem_x509_csr(pemcsr, default_backend())
           #print(csr)
           # issuer=pemcsr.issuer
           #cn = csrobj.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
           #o = csrobj.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME)[0].value
           attributes=[]
           for attribute in csrobj.subject:
               attributes.append(attribute.rfc4514_string())
           san = csrobj.extensions.get_extension_for_oid(
               x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
           #for dns_name in san.get_values_for_type(x509.DNSName):
           sans=[]
           for s in san.value:
               print(s)
               sans.append(s)
           context["id"] = id
           context["user"]= request.user
           context["role"]= request.user.get_role_display()
           context['pemcsr']= pemcsr
           context['pemkey']= pemkey
           context['csrobj']=csrobj
           context['attributes']=attributes
           context['sans'] = sans
           return render(request , "certs/generator.html",context)
        else:
            messages.add_message(
                request,
                messages.WARNING,
                f"Form not valid!",
            )
            context = {
                "id": id,
                "form": csrform,
                "user": request.user,
                "role": request.user.get_role_display(),
            }
            return render(request, "certs/gencsr.html", context)
    else:
        # This is the GET request
        record = Certificate.objects.get(id=id)
        print('calling readcert')
        data = readcert.readcert(record.fqdn,record.port)
        if data and 'Let\'s Encrypt'in data['issuer'] :
            messages.add_message(
                request,
                messages.WARNING,
                f"Issuer was Let's Encrypt which does not use CSR's",
                )
        if data and 'Google Trust'in data['issuer'] :
            messages.add_message(
                request,
                messages.WARNING,
                f"Issuer was Google which does not use CSR's",
                )

        if not data:
            data = {
                "common_name": "common name",
                "country_name": "GB",
                "state_or_province_name": "state or province",
                "organization_name": "organization name",
                "locality_name": "locality name",
                "subject_alternative_name": "name1,name2",
            }
            messages.add_message(
                request,
                messages.WARNING,
                f"Could not reach {record.fqdn}!",
                )
        csrform = CsrForm(data)
        context = {
            "id": id,
            "form": csrform,
            "user": request.user,
            "role": request.user.get_role_display(),
        }
        return render(request, "certs/gencsr.html", context)

@login_required
def download_key(request):
    url = request.GET.get("common_name")
    pemkey =  request.GET.get("pemkey"),
    response = HttpResponse(pemkey[0], content_type="application/txt")
    response['Content-Disposition'] = f'attachment; filename=key-{url}.txt'
    return response

@login_required
def download_csr(request):
    url = request.GET.get("common_name")
    pemcsr =  request.GET.get("pemcsr"),
    response = HttpResponse(pemcsr[0], content_type="application/txt")
    response['Content-Disposition'] = f'attachment; filename=csr-{url}.txt'
    return response

@login_required
def mail_all(request):
    # this has to run from cron so mail_contacts is the cron code
    # recalculate first though as ppl update all the time
    s = scripts.recalculate_all
    s.recalculate_all()
    mail_contacts()
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Mailed!",
    )
    return HttpResponseRedirect(reverse("certs:index"))

@login_required
def graphs(request):
    import pandas as pd
    import plotly.express as px
    import plotly
    from operator import itemgetter
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import json

    logging.basicConfig(level=logging.WARNING)
    logging.getLogger().setLevel(logging.DEBUG)
    #logging.getLogger().setLevel(logging.WARNING)

    queryset = Certificate.objects.order_by("expiry_date")

    size=1 # the effective height  of each block on the graph

    obj=Settings.objects.all().first()
    default_viewing_window = viewing_window  = obj.viewing_window
    daystogo_warning = obj.daystogo_warning

    try:
        v = int ( request.GET.get('viewing_window') ) 
        if v > 0:
            viewing_window = v 
        else:
           viewing_window =  v  
    except:
        viewing_window =  default_viewing_window 

    # mung the date field  Month Day Year for the graph
    display_these=[]
    for cert in queryset:
        if cert.expiry_date == "update daystogo":
           cert.expiry_date = "Jan 1 00:00:00 1976 GMT"
        cert_full_expiry_date  = cert.expiry_date
        cert_full_expiry_date_for_graph = cert.expiry_date.strftime('%A %H:%M  %Y-%m-%d')
        #cert_expiry_date_for_graph =cert.expiry_date.strftime('%b %d %Y')
        cert_shortname=cert.fqdn.split('.')
        display_these.append([  cert.fqdn,
                                cert.daystogo,
                                "ok",
                                cert.port,
                                cert_full_expiry_date_for_graph,
                                cert.contacts,
                                cert.grade,
                                size,
                                cert_shortname[0],
                              ])

    total=len(display_these)
    count=0
   
    warning_daystogo = daystogo_warning  # from settings
    warning_daystogo_yaxis = warning_daystogo + 0.5

    urgent_daystogo = 1 # fixed
    urgent_daystogo_yaxis = urgent_daystogo - 0.5

    def SetColor(i):
        x=float(i)
        if(x <= urgent_daystogo):
            return "urgent"
        elif(x > 1 and x <= warning_daystogo):
            return "warning"
        elif(x > warning_daystogo):
            return "ok"

    for c in display_these:
        c[2] = (SetColor(c[1]))

    df = pd.DataFrame( data=display_these,
                       columns=[    'fqdn',
                                    'daystogo',
                                    'color',
                                    'port',
                                    'expiry_date',
                                    'contacts',
                                    'grade',
                                    'size',
                                    'cert_shortname'])
    fig = px.bar(   df, 
                    x='daystogo',   
                    y='size',
                    barmode='stack',  
                    color = 'color',
                    color_discrete_map={
                            "urgent": "red",
                            "warning": "orange",
                            "ok": "green",},
                    text='cert_shortname',
                    custom_data= [  'fqdn', 
                                    'daystogo', 
                                    'color',
                                    'port', 
                                    'expiry_date', 
                                    'contacts', 
                                    'grade', 
                                    'size',
                                    'cert_shortname',
                                  ] 
                 )

    # we get this message with the above code
    """
    /Users/mb12aeh/Python/Django-Certiffy/venv/lib/python3.10/site-packages/plotly/express/_core.py:2065: FutureWarning
: When grouping with a length-1 list-like, you will need to pass a length-1 tuple to get_group in a future version
of pandas. Pass `(name,)` instead of `name` to silence this warning.
  sf: grouped.get_group(s if len(s) > 1 else s[0])
  """

    fig.update_traces(
        # width=1 cos width can vary for stacked charts
        width=1,
        hovertemplate=mark_safe('<br>'.join([
            "%{customdata[0]}:%{customdata[3]}",
            "daystogo=<b>%{customdata[1]}</b>",
            "grade=%{customdata[6]}",
            "%{customdata[4]}",
            "%{customdata[5]}",
        ])))


    earliest  = int ( df.iloc[0]['daystogo'] -1 )
    logging.debug(f'earliest={earliest}')
    fig.update_xaxes(range=[earliest, viewing_window +0.5  ])
    if viewing_window > 15 and viewing_window < 30:
        dtickvalue=7
    elif viewing_window > 30:
        dtickvalue=30
    else:
        dtickvalue=1

    fig.add_vline(  x=warning_daystogo_yaxis, 
                    line_width=3, 
                    line_dash="dash", 
                    line_color="orange",)
    fig.add_vline(  x=urgent_daystogo_yaxis, 
                    line_width=3, 
                    line_dash="dash", 
                    line_color="red",)

    fig.add_vrect(x0=urgent_daystogo_yaxis, x1=warning_daystogo_yaxis,
              annotation_text=" These certificates<br>need replacing", annotation_position="top left",
              fillcolor="orange", opacity=0.25, line_width=3)
    fig.add_vrect(x0=-30, x1=urgent_daystogo_yaxis,
              annotation_text="Expired Certs", annotation_position="top right",
              fillcolor="red", opacity=0.25, line_width=0)

    fig.update_layout(
        xaxis = dict(
            tick0 = 1,
            dtick = dtickvalue,
            ),
        yaxis = dict(
          title="",
          tickmode = 'linear',
          showticklabels = True,
          tick0 = 1,
          dtick = 1
     )
    )
    today = datetime.today()
    MonthDay=today.strftime("%d %b")

    fig.update_layout(
      title_font_family="Times New Roman",
      title_font_size=25,
      font=dict(
          size=14,
          color="Black"
       ),
      width=900,
      )
    """
      bargap=1,
      autosize=True,
      width=900,
      height=200,
      margin=dict(
        pad=0
        ),
    """

    fig.update_layout(
      hoverlabel=dict(
          bgcolor="lavender",
          bordercolor="gray",
          font_color="gray",
          font_size=18,
          font_family="Times New Roman"
      )
    )

    fig.update_layout(  title = 'Today: ' +  MonthDay  + " - Certificates window of " + str(viewing_window) + " days" , showlegend=False )
    
    fig.update_layout(modebar_remove="zoomin,zoomout,pan,lasso",plot_bgcolor="lavender")
    figJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    context = { 'figJSON':figJSON, 
                'viewing_window': viewing_window,
                'default_viewing_window': default_viewing_window,
                "role": request.user.get_role_display(),
                "user": request.user,
               }
    return render(request,"certs/graphs.html", context )



