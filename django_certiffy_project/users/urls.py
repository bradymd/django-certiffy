from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("register/", views.register, name="register"),
    path("detail/<id>", views.detail, name="detail"),
    path("delete/<id>", views.delete, name="delete"),
    path("update/<id>", views.update_view, name="update"),
    path("changeownpassword/", views.changeownpassword, name="changeownpassword"),
    path("resetpassword/<id>", views.resetpassword, name="resetpassword"),
    path("search/", views.search, name="search"),
    path("exportjson/", views.exportjson, name="exportjson"),
    path("importjson/", views.importjson, name="importjson"),
    path("deleteall/", views.deleteall, name="deleteall"),
]
