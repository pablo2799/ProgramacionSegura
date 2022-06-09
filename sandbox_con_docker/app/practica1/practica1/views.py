from curses.ascii import HT
from urllib import request
from django.http import HttpResponse, JsonResponse
from django.template import Template, Context
from django.shortcuts import render, redirect
from django.conf import settings


def login(request):
   request.session['logueado'] = True
   request.session['contador'] = 0
   t = 'login.html'
   return render(request,t)

def logout(request):
   request.session['logueado'] = False
   request.session.flush()
   return redirect('/registrar_maestros')

def pagina_restringida(request):
   contador = request.session.get('contador', '')
   if contador !='':
      request.session['contador'] = contador + 1
   if request.session.get('logueado', False) == True:
      return HttpResponse('puedes entrar %s' % contador)
   else:
      return HttpResponse('EStas bloqueado %s' % contador)

def registrar_maestros(request):
   t = 'registrar_maestros.html'
   if request.method == 'GET':
      return render(request,t) 

def registrar_alumnos(request):
   t = 'registrar_alumnos.html'
   if request.method == 'GET':
      return render(request,t)

def listar_ejercicios(request):
   contador = request.session.get('contador', '')
   if contador !='':
      request.session['contador'] = contador + 1
   if request.session.get('logueado', False) == True:
      t = 'listar_ejercicios.html'
      if request.method == 'GET':
         return render(request,t)
   else:
      return HttpResponse('No estas logueado')

def subir_ejercicio(request):
   t = 'subir_ejercicio.html'
   if request.method == 'GET':
      return render(request,t) 

def crear_ejercicios(request):
   t = 'crear_ejercicios.html'
   if request.method == 'GET':
      return render(request,t)

def revisar_ejercicio(request):
   t = 'revisar_ejercicio.html'
   if request.method == 'GET':
      return render(request,t) 

#def login(request):
#   request.session['logueado'] = True
#   t = 'login.html'
#   if request.method == 'GET':
#      logueado = request.session.get('logueado', False)
#      return render(request,t) 