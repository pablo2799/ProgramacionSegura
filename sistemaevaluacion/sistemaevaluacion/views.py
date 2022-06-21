from django.shortcuts import render, redirect
from modelos import models
import sistemaevaluacion.settings as conf
import datetime
from datetime import timezone
import random, string
import requests
from django.utils.crypto import get_random_string
import hashlib
from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
import logging
import os
import subprocess
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                     datefmt='%d-%b-%y %H:%M:%S',
                     level=logging.INFO,
                     filename='logs/registro-eventos.log',
                     filemode='a'

)

def get_client_ip(request:object):
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
   return tiempo_transcurrido.seconds

def mandar_mensaje_bot(request:object, tipousuario:str):
   """
   -Función que genera una cadena aleatoria de 4 caracteres para formar un token de autenticación
   -Manda el token al telegram del usuario
   -Guarda el token en la instancia del alumno o maestro
   -Obtiene la fecha actual para guardarla en la instancia del usuario
   -Argumentos:
      -Objeto request
      -Tipo de usuario que ingresó sus credenciales en el login
   """
   user = request.session['usuario']
   fecha_actual = datetime.datetime.now()
   template = 'login.html'
   if tipousuario=='alumno':
      obtener_datos = models.Alumnos.objects.get(usuario=user)
   elif tipousuario =='maestro':
      obtener_datos = models.Maestros.objects.get(usuario=user)
   mensaje = ''.join(random.sample(string.ascii_letters + string.digits, 6))
   send_text = 'https://api.telegram.org/bot' + obtener_datos.tokenId + '/sendMessage?chat_id=' + obtener_datos.chatId + '&parse_mode=Markdown&text=' + mensaje
   response = requests.get(send_text)
   registrar_token = obtener_datos
   registrar_token.token = mensaje
   registrar_token.vidaToken = fecha_actual
   registrar_token.save()
   logging.info(f"Se registró un nuevo token para el {tipousuario} {obtener_datos.usuario}")

def login(request:object):
   """
   -Vista que muestra la página para que un usuario (maestro o alumno) pueda iniciar sesión si está registrado en la base de datos
      -Los usuarios se identifican con su nombre, contraseña y tipo de usuario
      -Llama a la función 'get_client_ip' para obtener la dirección IP del cliente
      -Llama a la función 'puede_hacer_peticion' para saber si un usuario puede intentar iniciar sesión
         -Un usuario puede intentar iniciar sesión hasta 3 veces durante un minuto
      -Llama a la función 'password_valido' para saber si la contraseña ingresada es correcta
      -Llama a la función 'mandar_mensaje_bot' en caso de que el nombre y la contraseña sean correctos para generar un token de autenticación
   -Argumento: Objeto request
   -Returns:
      -Renderiza la plantilla HTML de la página si la petición fue de tipo GET
      -Renderiza la plantilla HTML de la página si la petición fue de tipo POST y/o hubo algún error durante la autenticación
      -Página de inicio de alumnos o de maestros si es que intentó entrar un usuario logueado
      -Redirige a la función 'comprobar_token_maestro' o 'comprobar_token_alumno' para finalizar la autenticación
   """
   template = 'login.html' 
   if request.method == 'GET': 
      if request.session.get('logueado', False) == True:
         user = request.session['usuario']
         if models.Alumnos.objects.filter(usuario__exact=user).count()>0:
            logging.info(f"El alumno {user} intentó entrar al login")
            return redirect('./inicio_alumnos')
         elif models.Maestros.objects.filter(usuario__exact=user).count()>0:
            logging.info(f"El maestro {user} intentó entrar al login")
            return redirect('./inicio_maestros')
      return render(request, template) 
   elif request.method == 'POST':
      datoIP = get_client_ip(request)
      if puede_hacer_peticion(datoIP): 
         usuario2 = request.POST.get('usuario1', '').strip() 
         password = request.POST.get('password', '').strip()
         tipousuario = request.POST.get('tipousuario', '').strip()
         errores = [] 
         if tipousuario == 'alumno':
            try:
               usuario = models.Alumnos.objects.get(usuario=usuario2)
            except ObjectDoesNotExist:
               errores = ['El alumno introducido no existe']
               logging.exception(f"No se inició sesión. Alumno incorrecto: {usuario2}")
               return render(request, template, {'errores': errores})
            if password_valido(password, usuario.password, usuario.salt):
               request.session['usuario'] = usuario2
               mandar_mensaje_bot(request, tipousuario)
               return redirect('./comprobar_token_alumno')
            else:
               errores = ['La contraseña introducida es incorrecta']
               logging.info(f"No se inició sesión. Contraseña incorrecta: {password}")
               return render(request, template, {'errores': errores})
         elif tipousuario =='maestro':
            try:
               usuario = models.Maestros.objects.get(usuario=usuario2)
            except ObjectDoesNotExist:
               errores = ['El maestro introducido no existe']
               logging.exception(f"No se inició sesión. Maestro incorrecto: {usuario2}")
               return render(request, template, {'errores': errores})
            if password_valido(password, usuario.password, usuario.salt):
               request.session['usuario'] = usuario2
               mandar_mensaje_bot(request, tipousuario)
               return redirect('./comprobar_token_maestro')
            else:
               errores = ['La contraseña introducida es incorrecta']
               logging.info(f"No se inició sesión. Contraseña incorrecta: {password}")
               return render(request, template, {'errores': errores})
         else:
            errores = ['Ocurrió un error al iniciar sesión']
            logging.error("No se pudo iniciar sesión")
            return render(request, template, {'errores': errores})
      else:
         errores = ['Número de intentos permitidos agotados, espera un momento']
         logging.info("Se hicieron muchos intentos de inicio de sesión para un usuario")
         return render(request,template, {'errores': errores})

def password_valido(contrasena_ingresada:str, contrasena_guardada:str, salt:str):
   """
   -Función que valida si la contraseña que ingresó el usuario es la misma que está guardada en la base de datos
      -Le agrega el salt que recibe como parámetro y hashea con el algoritmo 'sha-256' antes de comparar las contraseñas
   -Argumentos:
      -Contraseña que ingresa el usuario en texto plano
      -Contraseña de la instancia hasheada
      -Salt de la instancia
   -Returns:
      -True si las contraseñas comparadas son las mismas
      -False si las contraseñas comparadas no coinciden
   """
   binario_para_comparar = (contrasena_ingresada + salt).encode('utf-8')
   hashss = hashlib.sha256()
   hashss.update(binario_para_comparar)
   if contrasena_guardada == hashss.hexdigest():
      return True
   else:
      return False

def logout(request:object):
   """
   -Vista que termina la sesión de los usuarios
      -Cambia el valor del estado de login
      -Limpia todas las variables de la Cookie de sesión
   -Argumento: Objeto request
   -Returns:
      -Redirige a la página de inicio de sesión si se intentar entrar sin estar logueado o si se llama estando logueado
   """
   try:
      username = request.session['usuario']
   except KeyError:
      logging.exception("Un usuario intentó cerrar sesión sin estar logueado")
      return redirect('./login')
   request.session['logueado'] = False
   request.session.flush()
   logging.info(f"El usuario {username} cerró sesión")
   return redirect('/login')

def comprobar_token_alumno(request:object):
   t = 'verificacion.html'
   try:
      username = request.session['usuario']
   except KeyError:
      logging.exception("Un usuario intentó entrar a comprobar token de alumno mediante URL")
      return redirect('./login')
   if request.method == 'GET': 
      if request.session.get('logueado', False) == True:
         if models.Alumnos.objects.filter(usuario__exact=username).count()>0:
            logging.info(f"El alumno {username} intentó entrar a comprobar token de alumnos estando logueado")
            return redirect('./inicio_alumnos')
         elif models.Maestros.objects.filter(usuario__exact=username).count()>0:
            logging.info(f"El maestro {username} intentó entrar a comprobar token de alumnos estando logueado")
            return redirect('./inicio_maestros') 
      return render(request, t)
   elif request.method == 'POST':
      token1 = request.POST.get('token', '').strip()
      try:
         obtener_datos = models.Alumnos.objects.get(token=token1)
      except ObjectDoesNotExist:
         errores = ['Token de Telegram inválido']
         logging.exception(f"El alumno {username} falló su intento de token")
         return redirect('./logout')
      tiempoV = tiempo_de_vida(obtener_datos.vidaToken)
      if (tiempoV > 60):
         errores = ['Tiempo de vida del token expirado']
         return render(request, t, {'errores': errores})
      request.session['logueado'] = True
      request.session['tipouser'] = 'alumno'
      logging.info(f"El usuario {username} inició sesión")
      return redirect('./inicio_alumnos')

def comprobar_token_maestro(request:object):
   t = 'verificacion.html'
   try:
      username = request.session['usuario']
   except KeyError:
      logging.exception("Un usuario intentó entrar a comprobar token de maestros mediante URL")
      return redirect('./login')
   if request.method == 'GET': 
      if request.session.get('logueado', False) == True:
         if models.Alumnos.objects.filter(usuario__exact=username).count()>0:
            logging.info(f"El alumno {username} intentó entrar a comprobar token de maestros estando logueado")
            return redirect('./inicio_alumnos')
         elif models.Maestros.objects.filter(usuario__exact=username).count()>0:
            logging.info(f"El maestro {username} intentó entrar a comprobar token de maestros estando logueado")
            return redirect('./inicio_maestros') 
      return render(request, t)
   elif request.method == 'POST':
      token1 = request.POST.get('token', '').strip()
      try:
         obtener_datos = models.Maestros.objects.get(token=token1)
      except ObjectDoesNotExist:
         errores = ['Token de Telegram inválido']
         logging.exception(f"El maestro {username} falló su intento de token")
         return redirect('./logout')
      tiempoV = tiempo_de_vida(obtener_datos.vidaToken)
      if (tiempoV > 60):
         errores = ['Tiempo de vida del token expirado']
         return render(request, t, {'errores': errores})
      request.session['logueado'] = True
      request.session['tipouser'] = 'maestro' 
      logging.info(f"El usuario {username} inició sesión")
      return redirect('./inicio_maestros')

def registrar_maestros(request:object):
   """
   -Vista para registrar maestros en la base de datos mediante un formulario
      -Llama a la función 'existe_usuario' para saber si el nombre del maestro ya existe en la base de datos
      -Llama a la función 'validar_datos_maestros' para saber si todos los campos del formulario son correctos
      -Para la contraseña:
         -Agrega una cadena aleatoria de 16 caracteres llamada 'salt'
         -Guarda el resultado final hasheado con el algoritmo 'sha-256'
   -Argumento: Objeto request
   -Returns:
      -Página de inicio de alumnos o de maestros si es que intentó entrar un usuario logueado
      -Renderiza la plantilla HTML de la página si la petición fue de tipo GET
      -Renderiza la plantilla HTML si la petición fue de tipo POST y hubo algún error al realizar el registro
      -Página de login si se realizó correctamente el registro
   """
   template = 'registrar_maestros.html' 
   if request.method == 'GET': 
      if request.session.get('logueado', False) == True:
         user = request.session['usuario']
         if models.Alumnos.objects.filter(usuario__exact=user).count()>0:
            logging.info(f"El alumno {user} intentó entrar al registro de maestros")
            return redirect('./inicio_alumnos')
         elif models.Maestros.objects.filter(usuario__exact=user).count()>0:
            logging.info(f"El maestro {user} intentó entrar al registro de maestros")
            return redirect('./inicio_maestros') 
      return render(request, template) 
   elif request.method == 'POST':
      usuario = request.POST.get('nombre', '').strip()
      password = request.POST.get('password', '').strip()
      id_chat = request.POST.get('chatId', '').strip()
      token_bot = request.POST.get('token', '').strip()
      npersonal = request.POST.get('nopersonal', '').strip()
      email = request.POST.get('correo', '').strip()
      fecha=datetime.datetime.now()
      usuario3 = models.Maestros(usuario=usuario, password=password, nopersonal=npersonal, correo=email, chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha)
      errores = validar_datos_maestros(usuario3)
      tipouser = 'maestro'
      usuario_existente = existe_usuario(usuario,tipouser)
      if usuario_existente:
         logging.info("Falló el registro de un maestro")
         contexto = {'errores':usuario_existente, 'usuario':usuario}
         return render(request,template,contexto)
      if not errores:
         salt = get_random_string(length=16)
         binario = (password + salt).encode('utf-8')
         hashss = hashlib.sha256()
         hashss.update(binario)
         usuario = models.Maestros(usuario=usuario, password=hashss.hexdigest(), nopersonal=npersonal, correo=email, chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha, salt=salt)
         usuario.save()
         logging.info(f"Se registró un maestro: {usuario.usuario}")
         return redirect('/login')
      else:
         logging.info("Falló el registro de un maestro")
         contexto = {'errores':errores, 'usuario':usuario}
         return render(request,template,contexto)

def inicio_alumnos(request:object):
   """
   -Vista para la página de inicio de los alumnos
      -Página solo para alumnos
   -Argumento: Objeto request
   -Returns:
      -Renderiza la plantilla HTML después de que un alumno inició sesión
      -Página de inicio de maestros si un maestro intentó entrar
      -Página de login si un usuario no logueado intentó entrar
   """
   if request.session.get('logueado', False) == True:
      username = request.session['usuario']
      tipousuario = request.session['tipouser']
      if tipousuario == 'maestro':
         logging.info(f"El maestro {username} intentó entrar al inicio de alumnos")
         return redirect ('./inicio_maestros')
      t = 'inicio_alumnos.html'
      if request.method == 'GET':
         return render(request,t,{'userlog':username})
   else:
      logging.info("Se intentó entrar a inicio de alumnos sin estar logueado")
      return redirect('./login')

def inicio_maestros(request:object):
   """
   -Vista para la página de inicio de los maestros
      -Página solo para maestros
   -Argumento: Objeto request
   -Returns:
      -Renderiza la plantilla HTML después de que un maestro inició sesión
      -Página de inicio de alumnos si un alumno intentó entrar
      -Página de login si un usuario no logueado intentó entrar
   """
   if request.session.get('logueado', False) == True:
      username = request.session['usuario']
      tipousuario = request.session['tipouser']
      if tipousuario == 'alumno':
         logging.info(f"El alumno {username} intentó entrar al inicio de maestros")
         return redirect ('./inicio_alumnos')
      t = 'inicio_maestros.html'
      if request.method == 'GET':
         return render(request,t,{'userlog':username})
   else:
      logging.info("Se intentó entrar a inicio de maestros sin estar logueado")
      return redirect('./login')

def registrar_alumnos(request:object):
   """
   -Vista para registrar alumnos en la base de datos mediante un formulario
      -Llama a la función 'existe_usuario' para saber si el nombre del alumno ya existe en la base de datos
      -Llama a la función 'validar_datos_alumnos' para saber si todos los campos del formulario son correctos
      -Para la contraseña:
         -Agrega una cadena aleatoria de 16 caracteres llamada 'salt'
         -Guarda el resultado final hasheado con el algoritmo 'sha-256'
   -Argumento: Objeto request
   -Returns:
      -Página de inicio de alumnos o de maestros si es que intentó entrar un usuario logueado
      -Renderiza la plantilla HTML de la página si la petición fue de tipo GET
      -Renderiza la plantilla HTML si la petición fue de tipo POST y hubo algún error al realizar el registro
      -Página de login si se realizó correctamente el registro
   """ 
   template = 'registrar_alumnos.html' 
   if request.method == 'GET': 
      if request.session.get('logueado', False) == True:
         user = request.session['usuario']
         if models.Alumnos.objects.filter(usuario__exact=user).count()>0:
            logging.info(f"El alumno {user} intentó entrar al registro de alumnos")
            return redirect('./inicio_alumnos')
         elif models.Maestros.objects.filter(usuario__exact=user).count()>0:
            logging.info(f"El maestro {user} intentó entrar al registro de alumnos")
            return redirect('./inicio_maestros') 
      return render(request, template) 
   elif request.method == 'POST':
      usuario = request.POST.get('nombre', '').strip()
      password = request.POST.get('password', '').strip()
      id_chat = request.POST.get('chatId', '').strip()
      token_bot = request.POST.get('token', '').strip()
      matri = request.POST.get('matricula', '').strip()
      carrer = request.POST.get('carrera', '').strip()
      email = request.POST.get('correo', '').strip()
      fecha=datetime.datetime.now()
      usuario3 = models.Alumnos(usuario=usuario, password=password, matricula=matri, carrera=carrer, correo=email, chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha)
      errores = validar_datos_alumnos(usuario3)
      tipouser = 'alumno'
      usuario_existente = existe_usuario(usuario,tipouser)
      if usuario_existente:
         contexto = {'errores':usuario_existente, 'usuario':usuario}
         return render(request,template,contexto)
      if not errores:
         salt = get_random_string(length=16)
         binario = (password + salt).encode('utf-8')
         hashss = hashlib.sha256()
         hashss.update(binario)
         usuario = models.Alumnos(usuario=usuario, password=hashss.hexdigest(), matricula=matri, carrera=carrer, correo=email, chatId=id_chat, tokenId=token_bot, token='0', vidaToken=fecha, salt=salt)
         usuario.save()
         logging.info(f"Se registró un alumno: {usuario.usuario}")
         return redirect('/login')
      else:
         logging.info("Falló el registro de un alumno")
         contexto = {'errores':errores, 'usuario':usuario}
         return render(request,template,contexto)

def validar_datos_maestros(usuario:object):
   """
   -Función para validar los campos introducidos por un usuario al intentar registrarse como maestro
      -Se validan: nombre, contraseña, número de personal, correo, chat ID de telegram, token de telegram
      -Ningún campo puede quedar vacío
   -Argumento: Una instancia de la clase 'Maestros'
   -Return: Una lista, ya sea vacía o no dependiendo si hubo errores
   """
   caracteres_especiales = "º!#$%&/()=+-*"
   errores = []
   especial = 0
   minus = 0
   mayus = 0
   digito = 0
   for i in caracteres_especiales:
      for e in usuario.password:
         if e == i:
            especial = especial + 1
         if e.islower():
            minus = minus + 1
         if e.isupper():
            mayus = mayus + 1
         if e.isdigit():
            digito = digito + 1
   if len(usuario.usuario) < 3:
      errores.append('El nombre es muy corto')
   elif len(usuario.usuario) > 50:
      errores.append('El nombre es muy largo')
   if len(usuario.chatId) !=9:
      errores.append('El chatId no es correcto')
   if len(usuario.tokenId) != 46:
      errores.append('El token no es correcto')
   if usuario.password.find(' ') != -1:
      errores.append('La contraseña no debe contener espacios')
   if especial < 1:
      errores.append('La contraseña no tiene ningun caracter especial')
   if len(usuario.password) < 10:
      errores.append('La contraseña no tiene la longitud necesaria de 10 caracteres')
   if minus < 1:
      errores.append('La contraseña no tiene letras en minúsculas')
   if mayus < 1:
      errores.append('La contraseña no tiene letras en mayúsculas')
   if digito <1:
      errores.append('La contraseña no tiene ningún dígito')
   if len(usuario.nopersonal) != 5:
      errores.append('El número de personal debe tener 5 caracteres')
   if len(usuario.correo) < 8:
      errores.append('El correo no puede ser menor a 8 caracteres')
   elif len(usuario.correo) > 30:
      errores.append('El correo no puede ser mayor a 30 caracteres')
   return errores

def validar_datos_alumnos(usuario:object):
   """
   -Función para validar los campos introducidos por un usuario al intentar registrarse como alumno
      -Se validan: nombre, contraseña, matrícula, carrera, correo, chat ID de telegram, token de telegram
      -Ningún campo puede quedar vacío
   -Argumento: Una instancia de la clase 'Alumnos'
   -Return: Una lista, ya sea vacía o no dependiendo si hubo errores
   """
   caracteres_especiales = "º!#$%&/()=+-*"
   errores = []
   especial = 0
   minus = 0
   mayus = 0
   digito = 0
   for i in caracteres_especiales:
      for e in usuario.password:
         if e == i:
            especial = especial + 1
         if e.islower():
            minus = minus + 1
         if e.isupper():
            mayus = mayus + 1
         if e.isdigit():
            digito = digito + 1
   if len(usuario.usuario) < 3:
      errores.append('El nombre es muy corto')
   elif len(usuario.usuario) > 50:
      errores.append('El nombre es muy largo')
   if len(usuario.chatId) != 9:
      errores.append('El chatId no es correcto')
   if len(usuario.tokenId) != 46:
      errores.append('El token no es correcto')
   if usuario.password.find(' ') != -1:
      errores.append('La contraseña no debe contener espacios')
   if especial < 1:
      errores.append('La contraseña no tiene ningun caracter especial')
   if len(usuario.password) < 10:
      errores.append('La contraseña no tiene la longitud necesaria de 10 caracteres')
   if minus < 1:
      errores.append('La contraseña no tiene caracteres en minusculas')
   if mayus < 1:
      errores.append('La contraseña no tiene caracteres en mayusculas')
   if digito <1:
      errores.append('La contraseña no tiene ningún dígito')
   if len(usuario.matricula) != 9:
      errores.append('La matrícula debe tener 9 caracteres')
   if len(usuario.carrera) < 5:
      errores.append('La carrera es muy corta')
   elif len(usuario.carrera) > 40:
      errores.append('La carrera es muy larga')
   if len(usuario.correo) != 28:
      errores.append('El correo debe tener 28 caracteres')
   return errores

def listar_ejercicios_maestros(request:object):
   """
   -Vista para mostrar los ejercicios creados por un maestro
      -Página solo para maestros
   -Argumento: Objeto request
   -Returns:
      -Página de inicio de alumnos si un alumno intentó entrar
      -Página de login si un usuario no logueado intentó entrar
      -Renderiza la plantilla HTML si la petición fue con el método GET
   """
   if request.session.get('logueado', False) == True:
      user = request.session['usuario']
      tipousuario = request.session['tipouser']
      if tipousuario == 'alumno':
         logging.info(f"El alumno {user} intentó entrar a listar ejercicios de maestros")
         return redirect ('./listar_ejercicios_estudiantes')
      t = 'listar_ejercicios_maestros.html'
      if request.method == 'GET':
         listaEjercicios = models.Ejerciciosmaestros.objects.all()
         return render(request,t, {'ejercicios':listaEjercicios, 'userlog':user})
   else:
      logging.info("Se intentó entrar a listar ejercicios de maestros sin estar logueado")
      return redirect('./login')

def listar_ejercicios_estudiantes(request:object):
   """
   -Vista para mostrar los ejercicios creados por un maestro
      -Página solo para alumnos
   -Argumento: Objeto request
   -Returns:
      -Página de inicio de maestros si un maestro intentó entrar
      -Página de login si un usuario no logueado intentó entrar
      -Renderiza la plantilla HTML si la petición fue con el método GET
   """
   if request.session.get('logueado', False) == True:
      user = request.session['usuario']
      tipousuario = request.session['tipouser']
      if tipousuario == 'maestro':
         logging.info(f"El maestro {user} intentó entrar a listar ejercicios de estudiantes")
         return redirect ('/inicio_maestros')
      t = 'listar_ejercicios_estudiantes.html'
      if request.method == 'GET':
         listaEjercicios = models.Ejerciciosmaestros.objects.all()
         return render(request, t, {'ejercicios':listaEjercicios, 'userlog':user})
   else:
      logging.info("Se intentó entrar a listar ejercicios de estudiantes sin estar logueado")
      return redirect('./login')

def subir_ejercicio(request:object):
   """
   -Vista para que un alumno pueda subir un ejercicio
      -Página solo para alumnos
      -Recibe el ID de un ejercicio enviado mediante el formulario de listar ejercicios de estudiantes si la petición fue con el método GET
      -Si no hubo errores en la petición del método POST con el envío del formulario, guarda el archivo del estudiante
      -Crea una nueva instancia de 'Ejerciciosalumnos' guardando el archivo del estudiante, la instancia de 'Alumnos' y la instancia de 'Ejerciciosmaestros'
         -Deja vacíos los campos de 'resultadoFinal' y 'resultadoParametros'
      -Llama a la función 'evaluar_ejercicio' para llenar los campos pendientes
      -Si ocurrió un error durante la ejecución de la función 'evaluarEjercicio' se borra la instancia creada de 'Ejerciciosalumnos'
   -Argumento: Objeto request
   -Returns:
      -Página de inicio de maestros si un maestro intentó entrar
      -Página de login si un usuario no logueado intentó entrar
      -Página de inicio de alumnos si un alumno intentó entrar mediante la URL y no por la selección de un ejercicio
      -Página de listar ejercicios para alumnos:
         -Si un alumno intentó entrar para volver a subir el mismo ejercicio
         -Si dio 'click' en subir sin seleccionar un archivo mediante una petición con el método POST
         -Si ocurrió un error al evaluar un ejercicio
         -Si se evaluó correctamente el ejercicio
      -Renderiza la plantilla HTML si la petición fue con el método GET
   """
   if request.session.get('logueado', False) == True:
      user = request.session['usuario']
      tipousuario = request.session['tipouser']
      alumno = models.Alumnos.objects.get(usuario=user)
      if tipousuario == 'maestro':
         logging.info(f"El maestro {user} intentó entrar a subir ejercicio")
         return redirect ('/inicio_maestros')
      t = 'subir_ejercicio.html'
      try:
         idejercicio = request.GET["ejercicio"]
      except MultiValueDictKeyError:
         logging.exception(f"El alumno {user} intentó entrar por URL a subir ejercicio")
         return redirect('./inicio_alumnos')
      ejercicio = models.Ejerciciosmaestros.objects.get(id=idejercicio)
      if request.method == 'GET':
         if models.Ejerciciosalumnos.objects.filter(ejercicio=ejercicio,alumno=alumno).count()>0:
            logging.info(f"El alumno {alumno.usuario} quizo volver a subir el ejercicio {ejercicio.titulo}")
            return redirect('./listar_ejercicios_estudiantes')
         else:
            return render(request,t,{'ejercicio':ejercicio, 'userlog':user})
      elif request.method == 'POST':
         try:
            script = request.FILES["scriptalumno"]
         except MultiValueDictKeyError:
            logging.exception(f"Error al subir el archivo de un ejercicio del alumno {user}")
            return redirect('./listar_ejercicios_estudiantes')
         #if models.Ejerciciosalumnos.objects.filter(ejercicio=ejercicio,alumno=alumno).count()>0:
         #   ejercicioalumno_repetido = models.Ejerciciosalumnos.objects.filter(alumno=alumno, ejecicio=ejercicio)
         #   ejercicioalumno_repetido.delete()
         ejercicioalumno = models.Ejerciciosalumnos(alumno=alumno,ejercicio=ejercicio, scriptEstudiante=script)
         ejercicioalumno.save()
         logging.info(f"El alumno {user} subió el ejercicio {ejercicio.titulo}")
         try:
            evaluar_ejercicio(ejercicioalumno)
         except:
            logging.exception("Ocurrió un error al evaluar el script")
            ejercicioalumno.delete()
            return redirect('./listar_ejercicios_estudiantes')
         return redirect('./listar_ejercicios_estudiantes')
   else:
      logging.info("Se intentó entrar a subir ejercicio sin estar logueado")
      return redirect('./login') 

def crear_ejercicios(request:object):
   """
   -Vista para que los maestros puedan crear nuevos ejercicios
      -Página solo para maestros
      -Se suben 3 archivos obligatorios
      -Se suben 4 campos de texto, 2 de ellos obligatorios
      -Se llama a la función 'validar_datos_crear_ejercicio' para validar los campos de texto que sube un maestro
      -Si no hubo errores se crea una nueva instancia de 'Ejerciciosmaestros'
   -Argumento: Objeto request
   -Returns:
      -Página de inicio de alumnos si un alumno intentó entrar
      -Rederiza la plantilla HTML
         -Si el la petición fue con el método GET
         -Si no se subió algún archivo
         -Si se creó correctamente un ejercicio
         -Si no se llenó algún campo de texto obligatorio
      -Página de login si un usuario intentó entrar sin estar logueado
   """
   if request.session.get('logueado', False) == True:
      user = request.session['usuario']
      tipousuario = request.session['tipouser']
      if tipousuario == 'alumno':
         logging.info(f"El alumno {user} intentó entrar a crear ejercicios")
         return redirect ('./inicio_alumnos')
      t = 'crear_ejercicios.html'
      if request.method == 'GET':
         return render(request,t, {'userlog':user})
      elif request.method == 'POST':
         titulo = request.POST["titulo"]
         desc = request.POST["descripcion"]
         entrp = request.POST["entradaprueba"]
         salesp = request.POST["salidaesperada"]
         try:
            scriptini = request.FILES["scriptini"]
            scriptcomef = request.FILES["scriptcomef"]
            scriptcomp = request.FILES["scriptcomp"]
         except MultiValueDictKeyError:
            errores = []
            errores.append('Debe subir los archivos')
            contexto = {'errores':errores, 'usuario':'usuario'}
            logging.exception(f"Error al subir algún archivo para crear un ejercicio del maestro {user}")
            return render(request,t,contexto)
         ejercicio_sin_validar = models.Ejerciciosmaestros(titulo=titulo,descripcion=desc, entradaPrueba=entrp, salidaEsperada=salesp,scriptInicial=scriptini, scriptComprobacionEF=scriptcomef, scriptComprobacionP=scriptcomp)
         errores = validar_datos_crear_ejercicio(ejercicio_sin_validar)
         if not errores:
            ejercicio = models.Ejerciciosmaestros(titulo=titulo, descripcion=desc, entradaPrueba=entrp, salidaEsperada=salesp, scriptInicial=scriptini, scriptComprobacionEF=scriptcomef, scriptComprobacionP=scriptcomp)
            ejercicio.save()
            logging.info(f"Se creó el ejercicio {titulo} del maestro {user}")
            return render(request, t)
         else:
            contexto = {'errores':errores, 'usuario':'usuario'}
            logging.info(f"Error al llenar algún campo para crear un ejercicio del maestro {user}")
            return render(request,t,contexto)
   else:
      logging.info("Se intentó entrar a crear ejercicios sin estar logueado")
      return redirect('./login')

def revisar_ejercicio(request:object):
   """
   -Vista para mostrar el resultado de las evaluaciones de los ejercicios de los alumnos
      -Página solo para maestros
   -Argumento: Objeto request
   -Returns:
      -Página de inicio de alumnos si un alumno quizo entrar
      -Renderiza la plantilla HTML si la petición fue con el método GET
      -Página de login si un usuario no logueado intentó entrar
   """
   if request.session.get('logueado', False) == True:
      user = request.session['usuario']
      tipousuario = request.session['tipouser']
      if tipousuario == 'alumno':
         logging.info(f"El alumno {user} intentó entrar a revisar ejercicio")
         return redirect ('./inicio_alumnos')
      t = 'revisar_ejercicio.html'
      if request.method == 'GET':
         resultado_ejercicios = models.Ejerciciosalumnos.objects.all()
         return render(request,t, {'ejercicios':resultado_ejercicios,'userlog':user})
   else:
      logging.info("Se intentó entrar a subir ejercicio sin estar logueado")
      return redirect('./login')

def validar_datos_crear_ejercicio(ejercicio_sin_validar:object):
   """
   -Función para validar los campos del formulario para crear un ejercicio
      -Se validan los campos: titulo, descripción, entrada de prueba y salida esperada
   -Argumento: Instancia de 'Ejerciciosmaestros'
   -Return: Una lista, ya sea vacía o no dependiendo si hubo errores
   """
   errores = []
   if len(ejercicio_sin_validar.titulo) < 5:
      errores.append('El titulo es muy')
   elif len(ejercicio_sin_validar.titulo) > 50:
      errores.append('El titulo es muy largo')
   if len(ejercicio_sin_validar.descripcion) > 255:
      errores.append('La descripcion es muy larga')
   if len(ejercicio_sin_validar.entradaPrueba) < 1:
      errores.append('La entrada de prueba no debe quedar vacia')
   elif len(ejercicio_sin_validar.entradaPrueba) > 100:
      errores.append('La entrada de prueba es muy larga')
   if len(ejercicio_sin_validar.salidaEsperada) > 100:
      errores.append('La salida esperada es muy larga')
   return errores

def existe_usuario(usuario:str,tipousuario:str):
   """
   -Función para validar si el nombre de un usuario ya está registrado en la base de datos para maestros y alumnos
   -Argumentos:
      -Nombre del usuario que se quiere registrar
      -Tipo de usuario que se quiere registrar
   -Return: Una lista que contiene error si el nombre de un alumno o maestro ya existe en la base de datos
   """
   errores = []
   if tipousuario == 'maestro':
      if models.Maestros.objects.filter(usuario__exact=usuario).count()>0:
         errores.append('Un maestro con ese nombre ya existe')
         return errores
   elif tipousuario == 'alumno':
      if models.Alumnos.objects.filter(usuario__exact=usuario).count()>0:
         errores.append('Un alumno con ese nombre ya existe')
         return errores

def evaluar_ejercicio(ejercicio_alumno:object):
   logging.info(f"Se está evaluando el ejercicio {ejercicio_alumno.ejercicio.titulo} del alumno {ejercicio_alumno.alumno.usuario}...")
   script_inicializacion = ('media/'+str(ejercicio_alumno.ejercicio.scriptInicial))
   script_evaluacion_parametros = ('media/'+str(ejercicio_alumno.ejercicio.scriptComprobacionP))
   script_comprobacion_final = ('media/'+str(ejercicio_alumno.ejercicio.scriptComprobacionEF))
   script_alumno = ('media/'+str(ejercicio_alumno.scriptEstudiante))
   entrada = ejercicio_alumno.ejercicio.entradaPrueba
   salida = ejercicio_alumno.ejercicio.salidaEsperada

   inicializacion(script_inicializacion)

   if evaluar_parametros(script_evaluacion_parametros, script_alumno) == 0:
      ejercicio_alumno.resultadoParametros = 'Paso'
      ejercicio_alumno.save()
   else:
      ejercicio_alumno.resultadoParametros = 'No paso'
      ejercicio_alumno.save()

   if ejecutar_script(entrada, script_alumno, salida) !=0:
      ejercicio_alumno.resultadoFinal = 'No paso'
      ejercicio_alumno.save()
      logging.info(f"La evaluación del ejercicio {ejercicio_alumno.ejercicio.titulo} del alumno {ejercicio_alumno.alumno.usuario} se detuvo porque no produjo la salida esperada")
      return 0

   if comprobar_estado_final(script_comprobacion_final, entrada) == 0:
      ejercicio_alumno.resultadoFinal = 'Paso'
      ejercicio_alumno.save()
   else:
      ejercicio_alumno.resultadoFinal = 'No paso'
      ejercicio_alumno.save()

   logging.info(f"Se evaluó correctamente el ejercicio {ejercicio_alumno.ejercicio.titulo} del alumno {ejercicio_alumno.alumno.usuario}")

def inicializacion(script_inicializacion:str):
   os.system(f'chmod +x {script_inicializacion}')
   ejecutar_script_inicializacion = [script_inicializacion]
   ejecucion_script_inicializacion = subprocess.Popen(ejecutar_script_inicializacion, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   logging.info("El script de inicialización se ejecutó correctamente")

def evaluar_parametros(script_evaluacion_parametros:str,script_alumno:str):
   os.system(f'chmod +x {script_evaluacion_parametros}')
   os.system(f'chmod +x {script_alumno}')
   ejecutar_script_eval_param = [script_evaluacion_parametros, script_alumno]
   ejecucion_script_eval_param = subprocess.Popen(ejecutar_script_eval_param, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = ejecucion_script_eval_param.communicate()
   codigo_retorno = ejecucion_script_eval_param.returncode
   logging.info(f"El código de retorno que regresó la evaluación de parámetros fue {codigo_retorno}")
   return codigo_retorno

def ejecutar_script(entrada:str, script_alumno:str, salida:str):
   os.system(f'chmod +x {script_alumno}')
   ejecutar_script_alumno = [script_alumno, entrada]
   ejecucion_script_alumno = subprocess.Popen(ejecutar_script_alumno, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = ejecucion_script_alumno.communicate()
   if salida != '':
      salida_alumno = stdout.decode('utf-8').strip()
      logging.info(f"La salida esperada es {salida} y la salida del alumno fue {salida_alumno}")
      if salida == salida_alumno:
         return 0
      else:
         return 1
   codigo_retorno = ejecucion_script_alumno.returncode
   logging.info(f"El código de retorno que regresó la ejecución del script del alumno fue {codigo_retorno}")
   return codigo_retorno

def comprobar_estado_final(script_comprobacion_final:str, entrada:str):
   os.system(f'chmod +x {script_comprobacion_final}')
   ejecutar_script_comprobacion_f = [script_comprobacion_final, entrada]
   ejecucion_script_comprobacion_f = subprocess.Popen(ejecutar_script_comprobacion_f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = ejecucion_script_comprobacion_f.communicate()
   codigo_retorno = ejecucion_script_comprobacion_f.returncode
   logging.info(f"El código de retorno que regresó la comprobación de estado final fue {codigo_retorno}")
   return codigo_retorno
"""
def separar_entrada_prueba(entrada):
   for i in entrada:
      cont=0
      if i == ',':
         cont+=1
   if cont >=1:
      entradas=entrada.split(',')
      num_entradas=len(entradas)
"""