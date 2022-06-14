from ast import If
from django.template import Template, Context
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from modelos import models
import sistemaevaluacion.settings as conf
import datetime
from datetime import timezone
import random, string
import requests
import sys
from django.utils.crypto import get_random_string
import hashlib

def get_client_ip(request):
   x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
   if x_forwarded_for:
      ip = x_forwarded_for.split(',')[0]
   else:
      ip = request.META.get('REMOTE_ADDR')
   return ip

def es_ip_conocida(ip: str):
   """
   Determina si la ip ya está en la BD.

   Keyword Arguments:
   ip: str
   returns: bool
   """
   registros = models.Peticion.objects.filter(ip=ip)
   return len(registros) != 0

def guardar_peticion(ip: str, intentos: int):
    """
    Rutina para almacenar información de petición, considerando las reglas de bloqueo de peticiones.

    Keyword Arguments:
    ip: str
    intentos: int, es el valor a guardar de intentos
    returns: None
    """
    fecha_actual = datetime.datetime.now()
    if not es_ip_conocida(ip):
        entrada = models.Peticion(ip=ip, intentos=1,
                                  timestamp=fecha_actual)
        entrada.save()
        return
    registro = models.Peticion.objects.get(ip=ip)
    registro.intentos = intentos
    registro.timestamp = fecha_actual
    registro.save()


def esta_tiempo_en_ventana(timestamp):
    """
    basic description.

    Keyword Arguments:
    timestamp: datetime de referencia
    returns: bool
    """
    momento_actual = datetime.datetime.now(timezone.utc)
    resta = momento_actual - timestamp
    if resta.seconds < conf.VENTANA_SEGUNDOS_INTENTOS_PETICION:
        return True
    return False


def puede_hacer_peticion(ip):
    """
    Verdadero si la IP no ha alcanzado el límite de intentos.

    Keyword Arguments:
    ip --
    returns: Bool
    """
    if not es_ip_conocida(ip):
        guardar_peticion(ip, 1)
        return True
    registro = models.Peticion.objects.get(ip=ip)
    if not esta_tiempo_en_ventana(registro.timestamp):
        guardar_peticion(ip, 1)
        return True
    else:
        if (registro.intentos + 1) > conf.INTENTOS_MAXIMOS_PETICION:
            guardar_peticion(ip, registro.intentos + 1)
            return False
        else:
            guardar_peticion(ip, registro.intentos + 1)
            return True


def tiempo_de_vida(tiempo_registrado):
   timestamp = datetime.datetime.now(timezone.utc)
   tiempo_transcurrido = timestamp - tiempo_registrado
   #print('tiempo de vida timestamp: ',timestamp)
   print ('tiempo transcurrido: ',tiempo_transcurrido)
   return tiempo_transcurrido.seconds


def mandar_mensaje_bot(request):
   user = request.session['usuario']
   fecha_actual = datetime.datetime.now()
   if models.Alumnos.objects.filter(usuario__exact=user).count()>0:
      obtener_datos = models.Alumnos.objects.get(usuario=user)
   elif models.Maestros.objects.filter(usuario__exact=user).count()>0:
      obtener_datos = models.Maestros.objects.get(usuario=user)
   mensaje = ''.join(random.sample(string.ascii_letters + string.digits, 4))
   send_text = 'https://api.telegram.org/bot' + obtener_datos.tokenId + '/sendMessage?chat_id=' + obtener_datos.chatId + '&parse_mode=Markdown&text=' + mensaje
   response = requests.get(send_text)
   registrar_token = obtener_datos
   registrar_token.token = mensaje
   registrar_token.vidaToken = fecha_actual
   registrar_token.save()
   #print('fecha registrada en el token: ',fecha_actual)

def login(request):
   template = 'login.html' 
   if request.method == 'GET': 
      if request.session.get('logueado', False) == True:
         user = request.session['usuario']
         if models.Alumnos.objects.filter(usuario__exact=user).count()>0:
            return redirect('./inicio_alumnos')
         elif models.Maestros.objects.filter(usuario__exact=user).count()>0:
            return redirect('./inicio_maestros') 
      return render(request, template) 
   elif request.method == 'POST':
      datoIP = get_client_ip(request)
      if puede_hacer_peticion(datoIP): 
         usuario2 = request.POST.get('usuario1', '').strip() 
         password = request.POST.get('password', '').strip()
         tipousuario = request.POST.get('tipousuario', '').strip()
         print('***********',tipousuario,'**********')
         print('*************password de login', password)
         errores = [] 
         try:
            if tipousuario == 'alumno':
               print ('ENtro en alumno')
               usuario = models.Alumnos.objects.get(usuario=usuario2)
               if password_valido(password, usuario.password, usuario.salt):
                  print('*******Se validaron las contraseñas******')
                  request.session['usuario'] = usuario2
                  mandar_mensaje_bot(request)
                  return redirect('./verificacion')
               else:
                  errores = ['El Usuario o la Contraseña Son incorrectos']
                  return render(request, template, {'errores': errores})
            elif tipousuario =='maestro':
               print ('ENtro en maestro')
               usuario = models.Maestros.objects.get(usuario=usuario2)
               if password_valido(password, usuario.password, usuario.salt):
                  print('*******Se validaron las contraseñas******')
                  request.session['usuario'] = usuario2
                  mandar_mensaje_bot(request)
                  return redirect('./verificacion')
               else:
                  errores = ['El Usuario o la Contraseña Son incorrectos de maestro']
                  return render(request, template, {'errores': errores})
            else:
               errores = ['El Usuario o la Contraseña Son incorrectos de maestro 2']
               return render(request, template, {'errores': errores})
         except:
            print ('NO entro ni en alumno ni en maestro') 
            errores = ['El Usuario o la Contraseña Son incorrectos']
            return render(request, template, {'errores': errores})
      else:
         errores = ['Número de intentos permitidos agotados, espera un momento']
         return render(request,template, {'errores': errores})

def password_valido(contrasena_ingresada, contrasena_guardada, salt):
   binario_para_comparar = (contrasena_ingresada + salt).encode('utf-8')
   hashss = hashlib.sha256()
   hashss.update(binario_para_comparar)
   print('*********+contraseña guardada****', contrasena_guardada)
   print('*********+contraseña ingresada****', hashss.hexdigest())
   if contrasena_guardada == hashss.hexdigest():
      return True
   else:
      return False

def logout(request):
    request.session['logueado'] = False
    request.session.flush() #Termina la sesión
    return redirect('/login') #Redirige a la página de inicio de sesión

def pagina_restringida(request):
   contador = request.session.get('contador', '')
   if contador !='':
      request.session['contador'] = contador + 1
   if request.session.get('logueado', False) == True:
      return HttpResponse('puedes entrar %s' % contador)
   else:
      return HttpResponse('EStas bloqueado %s' % contador)

def comprobar_token(request):
   t = 'verificacion.html'
   try:
      username = request.session['usuario']
      if request.method == 'GET': 
         if request.session.get('logueado', False) == True:
            user = request.session['usuario']
            if models.Alumnos.objects.filter(usuario__exact=user).count()>0:
               return redirect('./inicio_alumnos')
            elif models.Maestros.objects.filter(usuario__exact=user).count()>0:
               return redirect('./inicio_maestros') 
         return render(request, t)
      elif request.method == 'POST':
         token1 = request.POST.get('token', '').strip()
         try:
            if models.Alumnos.objects.filter(usuario__exact=username).count()>0:
               obtener_datos = models.Alumnos.objects.get(token=token1)
               quieneres='alumno'
            elif models.Maestros.objects.filter(usuario__exact=username).count()>0:
               obtener_datos = models.Maestros.objects.get(token=token1)
               quieneres='maestro'
            tiempoV = tiempo_de_vida(obtener_datos.vidaToken)
            print('se obtiene el tiempo que transcurrido:', tiempoV)
            if (tiempoV > 60):
               print('Se manda tiempo expirado')
               errores = ['Tiempo de vida del token expirado']
               return render(request, t, {'errores': errores}) 
            request.session['logueado'] = True 
            request.session['usuario'] = username
            if quieneres == 'alumno': 
               return redirect('./inicio_alumnos')
            elif quieneres == 'maestro':
               return redirect('./inicio_maestros')
         except:
            errores = ['Token de Telegram inválido']
            return redirect('./logout')
   except:
      return redirect('./login')


def registrar_maestros(request):
   template = 'registrar_maestros.html' 
   if request.method == 'GET': 
      if request.session.get('logueado', False) == True:
         user = request.session['usuario']
         if models.Alumnos.objects.filter(usuario__exact=user).count()>0:
            return redirect('./inicio_alumnos')
         elif models.Maestros.objects.filter(usuario__exact=user).count()>0:
            return redirect('./inicio_maestros') 
      return render(request, template) 
   elif request.method == 'POST':
      print('***********entro POST**************')
      usuario = request.POST.get('nombre', '').strip()
      password = request.POST.get('password', '').strip()
      id_chat = request.POST.get('chatId', '').strip()
      token_bot = request.POST.get('token', '').strip()
      npersonal = request.POST.get('nopersonal', '').strip()
      email = request.POST.get('correo', '').strip()
      print ('*********password al registrar\n',password)
      fecha=datetime.datetime.now()
      usuario3 = models.Maestros(usuario=usuario, password=password, nopersonal=npersonal, correo=email, chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha)
      errores = validar_datos_maestros(usuario3)
      if not errores:
         print('*************NO hubo errores**********+')
         salt = get_random_string(length=16)
         binario = (password + salt).encode('utf-8')
         hashss = hashlib.sha256()
         hashss.update(binario)
         usuario = models.Maestros(usuario=usuario, password=hashss.hexdigest(), nopersonal=npersonal, correo=email, chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha, salt=salt)
         usuario.save()
         return redirect('/login')
      else:
         print('*************hubo errores****************')
         contexto = {'errores':errores, 'usuario':usuario}
         return render(request,template,contexto)

def inicio_alumnos(request):
   if request.session.get('logueado', False) == True:
      username = request.session['usuario']
      try:
         maestro = models.Alumnos.objects.get(usuario=username)
         t = 'inicio_alumnos.html'
         if request.method == 'GET':
            return render(request,t,{'userlog':username})
      except:
         return HttpResponse('Pagina solo para alumnos')
   else:
      return HttpResponse('No estas logueado')

def inicio_maestros(request):
   if request.session.get('logueado', False) == True:
      username = request.session['usuario']
      try:
         maestro = models.Maestros.objects.get(usuario=username)
         t = 'inicio_maestros.html'
         if request.method == 'GET':
            return render(request,t,{'userlog':username})
      except:
         return HttpResponse('Pagina solo para maestros')
   else:
      return HttpResponse('No estas logueado')

def registrar_alumnos(request): 
   template = 'registrar_alumnos.html' 
   if request.method == 'GET': 
      if request.session.get('logueado', False) == True:
         user = request.session['usuario']
         if models.Alumnos.objects.filter(usuario__exact=user).count()>0:
            return redirect('./inicio_alumnos')
         elif models.Maestros.objects.filter(usuario__exact=user).count()>0:
            return redirect('./inicio_maestros') 
      return render(request, template) 
   elif request.method == 'POST':
      print('***********entro POST**************')
      usuario = request.POST.get('nombre', '').strip()
      password = request.POST.get('password', '').strip()
      id_chat = request.POST.get('chatId', '').strip()
      token_bot = request.POST.get('token', '').strip()
      matri = request.POST.get('matricula', '').strip()
      carrer = request.POST.get('carrera', '').strip()
      email = request.POST.get('correo', '').strip()
      print ('*********password al registrar\n',password)
      fecha=datetime.datetime.now()
      usuario3 = models.Alumnos(usuario=usuario, password=password, matricula=matri, carrera=carrer, correo=email, chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha)
      errores = validar_datos_alumnos(usuario3)
      if not errores:
         print('*************NO hubo errores**********+')
         salt = get_random_string(length=16)
         binario = (password + salt).encode('utf-8')
         hashss = hashlib.sha256()
         hashss.update(binario)
         usuario = models.Alumnos(usuario=usuario, password=hashss.hexdigest(), matricula=matri, carrera=carrer, correo=email, chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha, salt=salt)
         usuario.save()
         return redirect('/login')
      else:
         print('*************hubo errores****************')
         contexto = {'errores':errores, 'usuario':usuario}
         return render(request,template,contexto)

def validar_datos_maestros(usuario):
      caracteres_especiales = "º!#$%&/()=+-*"
      errores = []
      especial = 0
      minus = 0
      mayus = 0
      digito = 0
      for i in caracteres_especiales:
         for e in usuario.password:
            if e == i:
               especial = especial + 1;
            if e.islower():
               minus = minus + 1;
            if e.isupper():
               mayus = mayus + 1;
            if e.isdigit():
               digito = digito + 1;
      if len(usuario.usuario) <= 0:
         errores.append('El nombre no puede quedar vacio')
      elif len(usuario.usuario) > 50:
         errores.append('El nombre es muy largo')
      if len(usuario.chatId) <= 0:
         errores.append('El chatId no debe quedar vacio')
      elif len(usuario.chatId) > 9:
         errores.append('El chatId es muy largo')
      if len(usuario.tokenId) <= 0:
         errores.append('El token no debe quedar vacio')
      elif len(usuario.tokenId) > 46:
         errores.append('El token es muy largo')
      if usuario.password.find(' ') != -1:
         errores.append('La contrasena no debe contener espacios')
      if especial <= 0:
         errores.append('La contrasena no tiene ningun caracter especial')
      if len(usuario.password) < 10:
         errores.append('La contrasena no tiene la longitud necesaria de 10 caracteres')
      if minus <= 0:
         errores.append('La contrasena no tiene caracteres en minusculas')
      if mayus <= 0:
         errores.append('La contrasena no tiene caracteres en mayusculas')
      if len(usuario.nopersonal) <= 0:
         errores.append('El numero de personal no puede quedar vacio')
      if len(usuario.nopersonal) > 5:
         errores.append('EL numero de personal es muy largo')
      if len(usuario.correo) <= 0:
         errores.append('El correo no puede quedar vacio')
      if len(usuario.correo) > 30:
         errores.append('El correo no puede quedar vacio')
 
      return errores
 
      return HttpResponse('Ok')

def validar_datos_alumnos(usuario):
      caracteres_especiales = "º!#$%&/()=+-*"
      errores = []
      especial = 0
      minus = 0
      mayus = 0
      digito = 0
      for i in caracteres_especiales:
         for e in usuario.password:
            if e == i:
               especial = especial + 1;
            if e.islower():
               minus = minus + 1;
            if e.isupper():
               mayus = mayus + 1;
            if e.isdigit():
               digito = digito + 1;
      if len(usuario.usuario) <= 0:
         errores.append('El nombre no puede quedar vacio')
      elif len(usuario.usuario) > 50:
         errores.append('El nombre es muy largo')
      if len(usuario.chatId) <= 0:
         errores.append('El chatId no debe quedar vacio')
      elif len(usuario.chatId) > 9:
         errores.append('El chatId es muy largo')
      if len(usuario.tokenId) <= 0:
         errores.append('El token no debe quedar vacio')
      elif len(usuario.tokenId) > 46:
         errores.append('El token es muy largo')
      if usuario.password.find(' ') != -1:
         errores.append('La contrasena no debe contener espacios')
      if especial <= 0:
         errores.append('La contrasena no tiene ningun caracter especial')
      if len(usuario.password) < 10:
         errores.append('La contrasena no tiene la longitud necesaria de 10 caracteres')
      if minus <= 0:
         errores.append('La contrasena no tiene caracteres en minusculas')
      if mayus <= 0:
         errores.append('La contrasena no tiene caracteres en mayusculas')
      if len(usuario.matricula) <= 0:
         errores.append('La matricula no puede quedar vacia')
      if len(usuario.matricula) > 9:
         errores.append('La matricula es muy larga')
      if len(usuario.carrera) <= 0:
         errores.append('La carrera no puede quedar vacia')
      if len(usuario.carrera) > 40:
         errores.append('La carrera es muy larga')
      if len(usuario.correo) <= 0:
         errores.append('El correo no puede quedar vacio')
      if len(usuario.correo) > 30:
         errores.append('El correo no puede quedar vacio')
      return errores

def listar_ejercicios_maestros(request):
   if request.session.get('logueado', False) == True:
      user = request.session['usuario']
      try:
         maestro = models.Maestros.objects.get(usuario=user)
         t = 'listar_ejercicios_maestros.html'
         if request.method == 'GET':
            listaEjercicios = models.Ejerciciosmaestros.objects.all()
            return render(request,t, {'ejercicios':listaEjercicios})
      except:
         return HttpResponse('Pagina solo para maestros')
   else:
      return HttpResponse('No estas logueado')

def listar_ejercicios_estudiantes(request):
   if request.session.get('logueado', False) == True:
      user = request.session['usuario']
      try:
         estudiante = models.Alumnos.objects.get(usuario=user)
         t = 'listar_ejercicios_estudiantes.html'
         if request.method == 'GET':
            listaEjercicios = models.Ejerciciosmaestros.objects.all()
            return render(request, t, {'ejercicios':listaEjercicios})
      except:
         return HttpResponse('Pagina solo para estudiantes')
   else:
      return HttpResponse('No estas logueado')

def subir_ejercicio(request):
   if request.session.get('logueado', False) == True:
      user = request.session['usuario']
      try:
         alumno = models.Alumnos.objects.get(usuario=user)
      except:
         return HttpResponse('Pagina solo para alumnos')
      t = 'subir_ejercicio.html'
      ejercicios = models.Ejerciciosmaestros.objects.all()
      if request.method == 'GET':
         return render(request,t,{'ejercicio':ejercicios})
      elif request.method == 'POST':
         script = request.FILES["scriptalumno"]
         ejercicio = models.Ejerciciosalumnos(scriptEstudiante=script)
         ejercicio.save()
         return render(request, t)
   else:
      return HttpResponse('No estas logueado') 

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
         try:
            titulo = request.POST["titulo"]
            desc = request.POST["descripcion"]
            entrp = request.POST["entradaprueba"]
            salesp = request.POST["salidaesperada"]
            scriptini = request.FILES["scriptini"]
            scriptcomef = request.FILES["scriptcomef"]
            scriptcomp = request.FILES["scriptcomp"]
         except:
            errores = []
            errores.append('Debe subir los archivos correctos')
            contexto = {'errores':errores, 'usuario':'usuario'}
            return render(request,t,contexto)
         ejercicio_sin_validar = models.Ejerciciosmaestros(titulo=titulo,descripcion=desc, entradaPrueba=entrp, salidaEsperada=salesp,scriptInicial=scriptini, scriptComprobacionEF=scriptcomef, scriptComprobacionP=scriptcomp)
         errores = validar_datos_crear_ejercicio(ejercicio_sin_validar)
         if not errores:
            print('*************NO hubo errores**********+')
            ejercicio = models.Ejerciciosmaestros(titulo=titulo, descripcion=desc, entradaPrueba=entrp, salidaEsperada=salesp, scriptInicial=scriptini, scriptComprobacionEF=scriptcomef, scriptComprobacionP=scriptcomp)
            ejercicio.save()
            return render(request, t)
         else:
            print('*************Hubo errores****************')
            contexto = {'errores':errores, 'usuario':'usuario'}
            return render(request,t,contexto)
   else:
      return HttpResponse('No estas logueado')

def revisar_ejercicio(request):
   if request.session.get('logueado', False) == True:
      user = request.session['usuario']
      try:
         maestro = models.Maestros.objects.get(usuario=user)
         t = 'revisar_ejercicio.html'
         if request.method == 'GET':
            return render(request,t)
      except:
         return HttpResponse('Pagina solo para maestros')
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