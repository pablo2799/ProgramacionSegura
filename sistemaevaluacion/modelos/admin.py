from django.contrib import admin

# Register your models here.
from .models import Peticion, Alumnos, Maestros

admin.site.register(Peticion)
admin.site.register(Alumnos)
admin.site.register(Maestros)