from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

app_name = "modelos"

urlpatterns = [
    path("", views.crear_ejercicios, name = "crear_ejercicios"),
]

if settings.DEBUG: 
    urlpatterns += static(
        settings.MEDIA_URL, 
        document_root = settings.MEDIA_ROOT
    )