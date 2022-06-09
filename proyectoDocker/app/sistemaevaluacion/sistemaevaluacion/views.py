from django.template import Template, Context
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from modelos import models
#from .models import Peticiones, Alumnos
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
   usuario = request.session['usuario']
   fecha_actual = datetime.datetime.now()
   obtener_datos = models.Alumnos.objects.get(usuario=usuario)
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
      logueado = request.session.get('logueado', False) 
        #if logueado: #Si está logueado redirige a la página que lista los Bots
         #   return redirect('./listar_ejercicios')
      return render(request, template) 
    elif request.method == 'POST': 
      usuario2 = request.POST.get('usuario1', '').strip() 
      password = request.POST.get('password', '').strip()
      print('*************password de login', password)
      errores = [] 
      try:
         usuario = models.Alumnos.objects.get(usuario=usuario2)
         if password_valido(password, usuario.password, usuario.salt):
            print('*******Se validaron las contraseñas******')
            #models.Alumnos.objects.get(usuario=usuario2, password=password) 
            #request.session['logueado'] = True 
            request.session['usuario'] = usuario2
            mandar_mensaje_bot(request)
            return redirect('./verificacion')
         else:
            errores = ['El Usuario o la Contraseña Son incorrectos']
            return render(request, template, {'errores': errores})
      except: 
         errores = ['El Usuario o la Contraseña Son incorrectos']
         return render(request, template, {'errores': errores}) 

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
   username = request.session['usuario']
   if request.method == 'GET':
      return render(request,t)
   elif request.method == 'POST':
      datoIP = get_client_ip(request)
      if puede_hacer_peticion(datoIP):
         token1 = request.POST.get('token', '').strip()
         try:
            obtener_datos = models.Alumnos.objects.get(token=token1)
            tiempoV = tiempo_de_vida(obtener_datos.vidaToken)
            print('se obtiene el tiempo que transcurrido:', tiempoV)
            if (tiempoV > 40):
               print('Se manda tiempo expirado')
               errores = ['Tiempo de vida del token expirado']
               #return redirect('./logout')
               return render(request, t, {'errores': errores}) 
            request.session['logueado'] = True 
            request.session['usuario'] = username
            request.session['contador'] = 0 
            return redirect('./subir_ejercicio')
         except:
            errores = ['Token de Telegram inválido']
            #return redirect('./logout')
            return render(request, t, {'errores': errores})
      else:
         errores = ['Número de intentos permitidos agotados, espera un momento']
         return render(request,t, {'errores': errores})


def registrar_maestros(request):
   t = 'registrar_maestros.html'
   if request.method == 'GET':
      return render(request,t)


def registrar_alumnos(request): 
   template = 'registrar_alumnos.html' 
   if request.method == 'GET':
      print ('***********entro al GET***********')
      return render(request, template) 
   elif request.method == 'POST':
      print('***********entro POST**************')
      usuario = request.POST.get('nombre', '').strip()
      password = request.POST.get('password', '').strip()
      id_chat = request.POST.get('chatId', '').strip()
      token_bot = request.POST.get('token', '').strip()
      print ('*********password al registrar\n',password)
      fecha=datetime.datetime.now()
      usuario3 = models.Alumnos(usuario=usuario, password=password, chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha)
      errores = validar_datos(usuario3)
      if not errores:
         print('*************NO hubo errores**********+')
         salt = get_random_string(length=16)
         binario = (password + salt).encode('utf-8')
         hashss = hashlib.sha256()
         hashss.update(binario)
         usuario = models.Alumnos(usuario=usuario, password=hashss.hexdigest(), chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha, salt=salt)
         usuario.save()
         return redirect('/login')
      else:
         print('*************hubo errores****************')
         contexto = {'errores':errores, 'usuario':usuario}
         return render(request,template,contexto)
      #registro=models.Alumnos()
      #registro.usuario = usuario
      #registro.password = password
      #registro.chatId = id_chat
      #registro.tokenId = token_bot
      #registro.token = '0'
      #registro.vidaToken = fecha
      #registro.salt = '0'
      #registro.save() #Guarda el registro nuevo
      #return render(request, "registrar_alumnos.html")

def validar_datos(usuario):
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
      if len(usuario.chatId) <= 0:
         errores.append('El chatId no debe quedar vacio')
      if len(usuario.tokenId) <= 0:
         errores.append('El token no debe quedar vacio')
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
 
      return errores
 
      return HttpResponse('Ok') 


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
   contador = request.session.get('contador', '')
   if contador !='':
      request.session['contador'] = contador + 1
   if request.session.get('logueado', False) == True:
      t = 'subir_ejercicio.html'
      if request.method == 'GET':
         return render(request,t)
   else:
      return HttpResponse('No estas logueado') 

def crear_ejercicios(request):
   contador = request.session.get('contador', '')
   if contador !='':
      request.session['contador'] = contador + 1
   if request.session.get('logueado', False) == True:
      t = 'crear_ejercicios.html'
      if request.method == 'GET':
         return render(request,t)
   else:
      return HttpResponse('No estas logueado')

def revisar_ejercicio(request):
   contador = request.session.get('contador', '')
   if contador !='':
      request.session['contador'] = contador + 1
   if request.session.get('logueado', False) == True:
      t = 'revisar_ejercicio.html'
      if request.method == 'GET':
         return render(request,t)
   else:
      return HttpResponse('No estas logueado')