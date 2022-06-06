from django.http import HttpResponse, JsonResponse
from django.template import Template, Context
from django.shortcuts import render, redirect
from django.conf import settings


def login(request):
   t = 'login.html'
   if request.method == 'GET':
      logueado = request.session.get('logueado', False)
      return render(request,t) 

def registrar_maestros(request):
   t = 'registrar_maestros.html'
   if request.method == 'GET':
      return render(request,t) 

def registrar_alumnos(request):
   t = 'registrar_alumnos.html'
   if request.method == 'GET':
      return render(request,t)

def listar_ejercicios(request):
   t = 'listar_ejercicios.html'
   if request.method == 'GET':
      return render(request,t)

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
