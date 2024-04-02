import logging,os

logger = logging.getLogger(__name__)
from django.shortcuts import (
    render,
    reverse,
    get_object_or_404,
    HttpResponseRedirect,
)
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MyUser
from .forms import  (RegistrationForm, 
                     UserUpdateForm, 
                     MyPasswordChangeForm, 
                     ResetPasswordForm,
                     UploadFileForm,
                     ExportFileForm)
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from certs.models import Certificate
from django.contrib.auth.models import AbstractUser, User
from django.contrib.auth.decorators import permission_required
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe



# Create your views here.

@login_required
def index(request):
    queryset = MyUser.objects.order_by("username")
    context = {
        "user_list": queryset,
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    return render(request, "users/index.html", context)


@login_required
@permission_required("users.add_myuser", raise_exception=False)
@permission_required("users.view_myuser", raise_exception=False)
def register(request):
    if request.method == "POST":
        try:
            form = RegistrationForm(request.POST)
        except:
            pass
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                f"Record {form.cleaned_data['username']} added successfully!",
            )
            if form.cleaned_data["role"] in ["USER", "ADMIN"]:
                u = form.cleaned_data["username"]
                myuser = MyUser.objects.get(username=u)
                role = myuser.role
                try:
                    u_group = Group.objects.get(name=role)
                except:
                    # if there is no USER or ADMIN group please create it
                    u_group = Group.objects.create(name=role)
                    # and assign permissions to add/delete/change certificates records
                    certificate_content_type = ContentType.objects.get_for_model(
                        Certificate
                    )
                    certificate_permissions = Permission.objects.filter(
                        content_type=certificate_content_type
                    )
                    for p in certificate_permissions:
                        u_group.permissions.add(p)
                    if str(u_group) == "ADMIN":
                        myuser_content_type = ContentType.objects.get_for_model(MyUser)
                        myusers_permissions = Permission.objects.filter(
                            content_type=myuser_content_type
                        )
                        for p in myusers_permissions:
                            u_group.permissions.add(p)
                myuser.groups.add(u_group)
                myuser.save()
                o = myuser.get_all_permissions()
                print(f"debug: {myuser}:{u_group}:{o}")
            context = {"user": request.user, "role": request.user.get_role_display()}
            return HttpResponseRedirect(reverse("users:index"))
        else:
            messages.warning(request, "Account registration failed")
    else:
        form = RegistrationForm()
    context = {
        "form": form,
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    return render(request, "users/register.html", context)


@login_required
@permission_required("users.view_myuser", raise_exception=True)
def detail(request, id):
    obj = get_object_or_404(MyUser, id=id)
    form = UserUpdateForm(request.POST or None, instance=obj)
    context = {
        "form": form,
        "id": id,
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    return render(request, "users/detail.html", context)


@login_required
@permission_required("users.delete_myuser", raise_exception=True)
def delete(request, id):
    u = MyUser.objects.get(id=id)
    username = u.username
    print("debug", u)
    u.delete()
    messages.add_message(
        request,
        messages.SUCCESS,
        f"User {username} deleted!",
    )
    return HttpResponseRedirect(reverse("users:index"))


@login_required
@permission_required("users.view_myuser")
def search(request):
    query = request.GET.get("username")
    print(f"username={query}")
    queryset = MyUser.objects.filter(username__icontains=query)
    context = {
        "user_list": queryset,
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    return render(request, "users/index.html", context)


@login_required
@permission_required("users.view_myuser", raise_exception=True)
@permission_required("users.change_myuser", raise_exception=True)
def update(request, id):
    obj = get_object_or_404(MyUser, id=id)
    form = UserUpdateForm(request.POST or None, instance=obj)
    context = {
        "form": form,
        "id": id,
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    return render(request, "users/update.html", context)


@login_required
@permission_required("users.view_myuser")
@permission_required("users.add_myuser")
@permission_required("users.change_myuser")
def update_view(request, id):
    obj = get_object_or_404(MyUser, id=id)
    # without instance=obj below, it will write a new instance
    form = UserUpdateForm(request.POST or None, instance=obj)
    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Record {form.cleaned_data['username']} updated!",
                )
                logging.debug('debug: in update_view making group match role')
                # this code is for the update view
                u=form.cleaned_data['username']
                user = MyUser.objects.get(username=u)
                user_groups = user.groups.all()
                user_groups_list=[]
                for g in user_groups:
                    user_groups_list.append(g.name)
                # might have to remove a group
                for g in user_groups:
                    if user.role != g.name:
                        g.user_set.remove(user)
                user_groups = user.groups.all()
                # might have to add a group
                if user.role in [ 'USER', 'ADMIN'] and user.role not in user_groups:
                        g  = Group.objects.get(name=user.role)
                        user.groups.add(g)
            except:
                messages.add_message(
                    request,
                    messages.ERROR,
                    f"Record {form.cleaned_data['username']} failed to update!",
                )
                print("form.is_valid but wouldnt save  debugging")
                for field in form:
                    logging.debug("Field Error:", field.name, field.errors)
            context = {
                "form": form,
                "id": id,
                "user": request.user,
                "role": request.user.get_role_display(),
            }
            return render(request, "users/update.html", context)
        else:
            for field in form:
                logging.debug("Field Error:", field.name, field.errors)
            logger.debug("Form is not valid then ... ")
            logger.warning(form.errors)
            messages.add_message(
                request,
                messages.WARNING,
                f"Record {form.cleaned_data['username']} DID NOT UPDATE!",
            )
            logger.debug("problem with the form")
            context = {
                "form": form,
                "id": id,
                "user": request.user,
                "role": request.user.get_role_display(),
            }
            return render(
                request, "users/update.html", context={"id": id, "form": form}
            )
    else:
        if request.method == "GET":
            # First click on Edit - there is no POST?
            context = {
                "form": UserUpdateForm(instance=obj),
                "id": id,
                "user": request.user,
                "role": request.user.get_role_display(),
            }
            return render(request, "users/update.html", context)


@login_required
# This is for the logged in user
def changeownpassword(request):
    user = request.user
    # me = MyUser.objects.filter(username=user)
    form = MyPasswordChangeForm(user=user, data=request.POST)
    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
                try:
                    # so you don't get logged out
                    update_session_auth_hash(request, user)
                except:
                    logging.debug("couldn't exectute update_session_auth_hash")
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Password for logged in user {user} updated!",
                )
            except:
                messages.add_message(
                    request, messages.ERROR, f"Password for {user} failed to update!"
                )
                logging.debug("form.is_valid but check for field errors")
                for field in form:
                    logging.debug("Field Error:", field.name, field.errors)
            return HttpResponseRedirect(reverse("certs:index"))
        else:
            for field in form:
                logging.debug("Field Error:", field.name, field.errors)
            logger.debug("Form is not valid then ... ")
            logger.warning(form.errors)
            messages.add_message(
                request,
                messages.WARNING,
                f"Record DID NOT UPDATE!",
            )
            logger.debug("problem with the form")
            context = {
                "form": form,
                "user": user,
                "role": request.user.get_role_display(),
            }
            return render(request, "users/changeownpassword.html", context)
    else:
        if request.method == "GET":
            # First click on Edit - there is no POST?
            context = {
                "form": form,
                "user": user,
                "role": request.user.get_role_display(),
            }
            return render(request, "users/changeownpassword.html", context)
@login_required
@permission_required("users.view_myuser")
@permission_required("users.add_myuser")
@permission_required("users.change_myuser")
# This is for the logged in user
def resetpassword(request,id):
    user = get_object_or_404(MyUser, id=id)
    form = ResetPasswordForm(user=user.username)
    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
                try:
                    # so you don't get logged out
                    update_session_auth_hash(request, user)
                except:
                    logging.debug("couldn't exectute update_session_auth_hash")
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Password for logged in user {user} updated!",
                )
            except:
                messages.add_message(
                    request, messages.ERROR, f"Password for {user} failed to update!"
                )
                logging.debug("form.is_valid but check for field errors")
                for field in form:
                    logging.debug("Field Error:", field.name, field.errors)
            return HttpResponseRedirect(reverse("certs:index"))
        else:
            for field in form:
                logging.debug("Field Error:", field.name, field.errors)
            logger.debug("Form is not valid then ... ")
            logger.warning(form.errors)
            messages.add_message(
                request,
                messages.WARNING,
                f"Record DID NOT UPDATE!",
            )
            logger.debug("problem with the form")
            context = {
                "form": form,
                "user": user,
                "role": request.user.get_role_display(),
            }
            return render(request, "users/resetpassword.html", context)
    else:
        if request.method == "GET":
            obj = get_object_or_404(MyUser, id=id)
            # First click on Edit - there is no POST?
            context = {
                "id" : id,
                "form": form,
                "user": obj.username,
                "role": request.user.get_role_display(),
            }
            return render(request, "users/resetpassword.html", context)


@login_required
@csrf_exempt
@permission_required("users.view_user")
@permission_required("users.add_user")
@permission_required("users.delete_user")
@permission_required("users.change_user")
def exportjson(request):
      def dump_table(table):
          from django.core import management
          from contextlib import redirect_stdout
          import io
          f = io.StringIO()
          with redirect_stdout(f):
            management.call_command("dumpdata", table,stdout=f)
          output = f.getvalue()
          return output

      if request.POST:
          filename = request.POST.get("file")
          # the csv file cant get the encrypted fields so is not a full dump
          # so we can use a dumpdata
          output=dump_table("users.MyUser")
          filenamejson =os.path.splitext(filename)[0]+'.json'
          response = HttpResponse(output, content_type="text/json;charset=utf-8")
          response["Content-Disposition"] = 'attachment;filename=' + filenamejson
          return response
      else:
        context = {
            "user": request.user,
            "role": request.user.get_role_display(),
        }
        return render(request, "users/export.html", context)

@login_required
@csrf_exempt
@permission_required("users.view_user")
@permission_required("users.add_user")
@permission_required("users.delete_user")
@permission_required("users.change_user")
def importjson(request):
      def handle_uploaded_file(f):
          with open("imported.json","wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)
      def load_table(file):
          from django.core import management
          from contextlib import redirect_stdout
          import io
          f = io.StringIO()
          with redirect_stdout(f):
              try:
                management.call_command("loaddata", file, stdout=f)
              except Exception as e:
                logging.debug(f'Error in management.call_command {e}')
                output=f"Problem: {e}"
                return output
          output = f.getvalue()
          return output
      context = {
            "user": request.user,
            "role": request.user.get_role_display(),
            "form": UploadFileForm(),
      }
      if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
          # upload the a file and leave it in imported.json
          handle_uploaded_file(request.FILES['file'])
          output=load_table("imported.json")
          if "Problem" in output:
                messages.add_message(
                    request,
                    messages.WARNING,
                    f"Failed to load.  {output}",
                )
          else:
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Success",
                )
          return HttpResponseRedirect(reverse("users:index"))
        else:
          messages.add_message(
                request,
                messages.SUCCESS,
                f"Form not valid!",
            )
          return render(request, "users/import.html", context)
      else:
        context = {
            "user": request.user,
            "role": request.user.get_role_display(),
            "form": UploadFileForm(),
           }
        return render(request, "users/import.html", context)

@login_required
@csrf_exempt
@permission_required("users.view_user")
@permission_required("users.add_user")
@permission_required("users.delete_user")
@permission_required("users.change_user")
def deleteall(request):
    context = {
        "user": request.user,
        "role": request.user.get_role_display(),
    }
    if request.method == "POST" and request.user.is_superuser:
       queryset = MyUser.objects.all()
       for u in queryset:
           if u.username != "admin":
              u.delete()
       messages.add_message(
                request,
                messages.SUCCESS,
                f"All  deleted!",
                )
       return HttpResponseRedirect(reverse("users:index"))
    else:
       messages.add_message(
                request,
                messages.SUCCESS,
                f"Form not valid!",
            )
       return HttpResponseRedirect(reverse("users:index"))


