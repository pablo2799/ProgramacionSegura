from django.http import HttpResponse, JsonResponse
from django.template import Template, Context
from django.shortcuts import render, redirect
from django.conf import settings
from modelos import models
from django.utils.crypto import get_random_string
import hashlib
import os


def registro(request):
     t = 'registro.html'; 
     if request.method == 'GET': 
        return render(request,t,{}) 
     elif request.method == 'POST': 
         nombre = request.POST.get('nombre','').strip() 
         matricula = request.POST.get('matricula','').strip() 
         contrasena =  request.POST.get('contrasena','').strip()
         usuario = models.Usuarios(Nombre=nombre, Matricula=matricula, Contrasena=contrasena)
         errores = validar_datos(usuario)
         if not errores:
            Salt = get_random_string(length=16) 
            binario = (contrasena + Salt).encode('utf-8') 
            hashss = hashlib.sha256() 
            hashss.update(binario) 
            usuario = models.Usuarios(Nombre=nombre, Matricula=matricula, Contrasena=hashss.hexdigest(), Salt=Salt) 
            usuario.save() 
            return redirect('/login')
         else: 
            contexto = {'errores':errores, 'usuario':usuario} 
            return render(request,t,contexto)
      

def validar_datos(usuario):
      caracteres_especiales = "º!#$%&/()=+-*"
      errores = []
      especial = 0
      minus = 0
      mayus = 0
      digito = 0
      for i in caracteres_especiales:
         for e in usuario.Contrasena:
            if e == i:
               especial = especial + 1;
            if e.islower():
               minus = minus + 1;
            if e.isupper():
               mayus = mayus + 1;
            if e.isdigit():
               digito = digito + 1;

      if len(usuario.Nombre) <= 0:
         errores.append('El nombre no puede quedar vacio')
      if len(usuario.   Matricula) <= 0:
         errores.append('La matricula no debe quedar vacia')
      if usuario.Contrasena.find(' ') != -1:
         errores.append('La contrasena no debe contener espacios')
      if especial <= 0:
          errores.append('La contrasena no tiene ningun caracter especial')
      if len(usuario.Contrasena) < 10:
         errores.append('La contrasena no tiene la longitud necesaria de 10 caracteres')
      if minus <= 0:
         errores.append('La contrasena no tiene caracteres en minusculas')
      if mayus <= 0:
         errores.append('La contrasena no tiene caracteres en mayusculas')

      return errores

      return HttpResponse('Ok')

def login(request):  
  logueado = request.session.get('logueado', False)
  if request.method == 'GET':
      print('cato')
      return render(request, 'login.html', {'logueado':logueado})
  elif request.method == 'POST':
        errores = []
        nombre = request.POST.get('Nombre', '')
        contraseña = request.POST.get('password', '')
        print('caaaaaaaaaaaaaato')
        if nombre and contraseña:
            try:    
               usuario = models.Usuarios.objects.get(Nombre=nombre)
               if password_valido(contraseña, usuario.Contrasena, usuario.Salt):
                  request.session['logueado']= True
                  request.session['nombre']= nombre
               else:
                  errores.append('Usuario o contraseña inválidos')
            except:
                  errores.append('Usuario o contraseña inválidos')
        else:        
            errores.append('No se pasaron las variables correctas en el formulario')
        return render(request, 'login.html', {'errores': errores})

def password_valido(contraseña_ingresada, contraseña_guardada, Salt):
            binario_para_comparar = (contraseña_ingresada + Salt).encode('utf-8') 
            hashss = hashlib.sha256() 
            hashss.update(binario_para_comparar)
            print(contraseña_guardada)
            print(hashss.hexdigest())
            if contraseña_guardada == hashss.hexdigest():
               return True
            else:
               return False

def logout(request):
    request.session.flush()
    return redirect('/login')