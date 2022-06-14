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
            try:
                scriptini = request.FILES["scriptini"]
                scriptcomef = request.FILES["scriptcomef"]
                scriptcomp = request.FILES["scriptini"]
            except:
                errores = []
                errores.append('Debe subir los archivos correctos')
                contexto = {'errores':errores, 'usuario':'usuario'}
                return render(request,t,contexto)
                return HttpResponse('Pagina solo para maestros')
            ejercicio_sin_validar = models.Ejerciciosmaestros(titulo=titulo, descripcion=desc, entradaPrueba=entrp, salidaEsperada=salesp, scriptInicial=scriptini, scriptComprobacionEF=scriptcomef, scriptComprobacionP=scriptcomp)
            errores = validar_datos_crear_ejercicio(ejercicio_sin_validar)
            if not errores:
                print('*************NO hubo errores**********+')
                ejercicio = models.Ejerciciosmaestros(titulo=titulo, descripcion=desc, entradaPrueba=entrp, salidaEsperada=salesp, scriptInicial=scriptini, scriptComprobacionEF=scriptcomef, scriptComprobacionP=scriptcomp)
                ejercicio.save()
                return render(request, 'crear_ejercicios.html')
            else:
                print('*************Hubo errores****************')
                contexto = {'errores':errores, 'usuario':'usuario'}
                return render(request,t,contexto)
    else:
        return HttpResponse('No estas logueado')
        

def validar_datos_crear_ejercicio(ejercicio_sin_validar):
    errores = []
    if len(ejercicio_sin_validar.titulo) <= 0:
        errores.append('El titulo no puede quedar vacio')
    elif len(ejercicio_sin_validar.titulo) > 20:
        errores.append('El titulo es muy largo')
    if len(ejercicio_sin_validar.descripcion) <= 0:
        errores.append('La descripcion no debe quedar vacia')
    elif len(ejercicio_sin_validar.descripcion) > 255:
        errores.append('La descripcion es muy larga')
    if len(ejercicio_sin_validar.entradaPrueba) <= 0:
        errores.append('La entradaPrueba no debe quedar vacia')
    elif len(ejercicio_sin_validar.entradaPrueba) > 100:
        errores.append('La entradaPrueba es muy larga')
    if len(ejercicio_sin_validar.salidaEsperada) <= 0:
        errores.append('La salidaEsperada no debe quedar vacia')
    elif len(ejercicio_sin_validar.salidaEsperada) > 100:
        errores.append('La salidaEsperada es muy larga')
    return errores
 
    return HttpResponse('Ok')

def subir_ejercicio(request):
    if request.session.get('logueado', False) == True:
        user = request.session['usuario']
        try:
            estudiante = models.Alumnos.objects.get(usuario=user)
        except:
            return HttpResponse('Pagina solo para estudiantes')
        t = 'subir_ejercicio.html'
        if request.method == 'GET':
            return render(request,t)
        elif request.method == 'POST':
            titulo = request.POST["titulo"]
            try:
                scriptEst = request.FILES["scriptEst"]
            except:
                errores = []
                errores.append('Debe subir el scrip correcto')
                contexto = {'errores':errores, 'usuario':'usuario'}  
            ejercicio_sin_validar = models.Ejerciciosalumnos(titulo=titulo, scriptEstudiante=scriptEst, resultadoFinal='resultadoF', resultadoParametros='resultadoP')
            errores = validar_datos_subir_ejercicio(ejercicio_sin_validar)
            if not errores:
                print('*************NO hubo errores**********+')
                ejercicio = models.Ejerciciosalumnos(titulo=titulo, scriptEstudiante=scriptEst, resultadoFinal='resultadoF', resultadoParametros='resultadoP')
                ejercicio.save()
                return render(request, 'crear_ejercicios.html')
            else:
                print('*************Hubo errores****************')
                contexto = {'errores':errores, 'usuario':'usuario'}
                return render(request,t,contexto)
    else:
        return HttpResponse('No estas logueado')

def validar_datos_subir_ejercicio(ejercicio_sin_validar):
    errores = []
    if len(ejercicio_sin_validar.titulo) <= 0:
        errores.append('El titulo no puede quedar vacio')
    elif len(ejercicio_sin_validar.titulo) > 20:
        errores.append('El titulo es muy largo')
    return errores
 
    return HttpResponse('Ok')