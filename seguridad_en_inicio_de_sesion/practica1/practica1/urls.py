"""practica1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from practica1.views import *
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',RedirectView.as_view(url='login', permanent=True)),
    path('login',login),
    path('logout', logout),
    path('enviar', mandar_mensaje_bot),
    path('verificacion',comprobar_token),
    path('registrar_maestros',registrar_maestros),
    path('registrar_alumnos',registrar_alumnos),
    path('listar_ejercicios',listar_ejercicios),
    path('subir_ejercicio',subir_ejercicio),
    path('crear_ejercicios',crear_ejercicios),
    path('revisar_ejercicio',revisar_ejercicio),
]
