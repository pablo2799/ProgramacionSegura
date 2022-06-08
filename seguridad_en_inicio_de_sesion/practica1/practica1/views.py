from django.template import Template, Context
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from modelo import models
#from .models import Peticiones, Alumnos
import practica1.settings as conf
import datetime
from datetime import timezone
import random, string
import requests
import sys


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
      try:
         models.Alumnos.objects.get(usuario=usuario2, password=password) 
         request.session['logueado'] = True 
         request.session['usuario'] = usuario2 
         mandar_mensaje_bot(request)
         return redirect('./verificacion') 
      except: 
         errores = ['El Usuario o la Contraseña Son incorrectos']
         return render(request, template, {'errores': errores}) 


def logout(request):
    request.session.flush() #Termina la sesión
    return redirect('/login') #Redirige a la página de inicio de sesión


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
      return render(request, template) 
   elif request.method=='POST':
      usuario = request.POST.get('nombre', '').strip()
      password = request.POST.get('password', '').strip()
      id_chat = request.POST.get('chatId', '').strip()
      token_bot = request.POST.get('token', '').strip()
      registro=models.Alumnos()
      registro.usuario = usuario
      registro.password = password
      registro.chatId = id_chat
      registro.tokenId = token_bot
      registro.save() #Guarda el registro nuevo
      return render(request, "registrar_alumnos.html") 


def listar_ejercicios(request):
   t = 'listar_ejercicios.html'
  # if request.method == 'GET':
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