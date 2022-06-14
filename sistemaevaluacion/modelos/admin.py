from django.contrib import admin

# Register your models here.
from .models import Peticion, Alumnos, Maestros, Ejerciciosmaestros, Ejerciciosalumnos

admin.site.register(Peticion)
admin.site.register(Alumnos)
admin.site.register(Maestros)
admin.site.register(Ejerciciosmaestros)
admin.site.register(Ejerciciosalumnos)
