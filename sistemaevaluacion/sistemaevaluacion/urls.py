"""sistemaevaluacion URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from sistemaevaluacion.views import *
from django.views.generic import RedirectView
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',RedirectView.as_view(url='login', permanent=True)),
    path('login',login),
    path('registrar_alumnos',registrar_alumnos),
    path('registrar_maestros',registrar_maestros),
    path('listar_ejercicios_estudiantes',listar_ejercicios_estudiantes),
    path('listar_ejercicios_maestros',listar_ejercicios_maestros),
    path('subir_ejercicio',subir_ejercicio),
    path('crear_ejercicios',crear_ejercicios),
    path('revisar_ejercicio',revisar_ejercicio),
    path('logout',logout),
    path('verificacion',comprobar_token),
    path('pagina_restringida',pagina_restringida),
    path('inicio_alumnos',inicio_alumnos),
    path('inicio_maestros',inicio_maestros),
]
if settings.DEBUG: 
    urlpatterns += static(
        settings.MEDIA_URL, 
        document_root = settings.MEDIA_ROOT
    )