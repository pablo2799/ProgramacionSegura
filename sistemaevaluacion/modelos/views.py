from django.shortcuts import render
from django.http import HttpResponse
from modelos import models
# Create your views here.
def crear_ejercicios(request):
    if request.session.get('logueado', False) == True:
        user = request.session['usuario']
        try:
            maestro = models.Maestros.objects.get(usuario=user)
        except:
            return HttpResponse('Pagina solo para maestros')
        t = 'crear_ejercicios.html'
        if request.method == 'GET':
            return render(request,t)
        elif request.method == 'POST':
            titulo = request.POST["titulo"]
            desc = request.POST["descripcion"]
            entrp = request.POST["entradaprueba"]
            salesp = request.POST["salidaesperada"]
            scriptini = request.FILES["scriptini"]
            scriptcomef = request.FILES["scriptcomef"]
            scriptcomp = request.FILES["scriptcomp"]
            ejercicio = models.Ejerciciosmaestros(titulo=titulo,descripcion=desc, entradaPrueba=entrp, salidaEsperada=salesp,scriptInicial=scriptini, scriptComprobacionEF=scriptcomef, scriptComprobacionP=scriptcomp)
            ejercicio.save()
            return render(request, 'crear_ejercicios.html')
    else:
        return HttpResponse('No estas logueado')