from django.urls import path, re_path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("create/", views.create, name="create"),
    path('detail/<id>', views.detail, name="detail"),
    path('update/<id>', views.update, name="update"),
    path('checkexpiry/<id>', views.checkexpiry, name="checkexpiry"),
    path('grade/<id>', views.grade, name="grade"),
    path('delete/<id>', views.delete, name="delete"),
    path('recalculate_all', views.recalculate_all, name="recalculate_all"),
    path('importcsv', views.importcsv, name="importcsv"),
    path('exportcsv', views.exportcsv, name="exportcsv"),
    path('deleteall', views.deleteall, name="deleteall"),
    path('mail/<id>', views.mail, name="mail"),
    path('mail_all', views.mail_all, name="mail_all"),
    path('gencsr/<id>', views.gencsr, name="gencsr"),
    path('settings', views.settings, name="settings"),
    path('download_key', views.download_key, name="download_key"),
    path('download_csr', views.download_csr, name="download_csr"),
    path('graphs/', views.graphs, name="graphs"),

]
