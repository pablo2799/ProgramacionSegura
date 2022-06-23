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
import socket
import os
import re
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
      -Llama a la función 'validar_nopersonal' para comprobar el formato del número de personal
      -Llama a la función 'validar_correo_maestros' para comprobar el formato del correo del maestro
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
   elif validar_nopersonal(usuario.nopersonal) == None:
      errores.append('El número de personal es incorrecto')
   if len(usuario.correo) < 10:
      errores.append('El correo no puede ser menor a 8 caracteres')
   elif len(usuario.correo) > 30:
      errores.append('El correo no puede ser mayor a 30 caracteres')
   elif validar_correo_maestros(usuario.correo) == None:
      errores.append('Formato de correo incorrecto')
   return errores

def validar_nopersonal(nopersonal:str):
   """
   -Función que valida si un número de personal tiene el formato correcto utilizando una expresión regular
   -Argumento: El número de personal que ingresa el maestro en el formulario de registro
   -Return: Si hubo o no coincidencia
   """
   regex = re.compile('^[0-9]{5}$')
   return (regex.match(nopersonal))

def validar_correo_maestros(correo:str):
   """
   -Función que valida si un correo de maestro tiene el formato correcto utilizando una expresión regular
   -Argumento: El correo que ingresa el maestro en el formulario de registro
   -Return: Si hubo o no coincidencia
   """
   regex = re.compile('^[a-z]{4,24}@uv.mx$')
   return (regex.match(correo))

def validar_datos_alumnos(usuario:object):
   """
   -Función para validar los campos introducidos por un usuario al intentar registrarse como alumno
      -Se validan: nombre, contraseña, matrícula, carrera, correo, chat ID de telegram, token de telegram
      -Ningún campo puede quedar vacío
      -Llama a la función 'validar_matricula' para comprobar el formato de la matrícula
      -Llama a la función 'validar_correo_alumnos' para comprobar el formato del correo del alumno
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
   elif validar_matricula(usuario.matricula) == None:
      errores.append('Matricula incorrecta')
   if len(usuario.carrera) < 5:
      errores.append('La carrera es muy corta')
   elif len(usuario.carrera) > 40:
      errores.append('La carrera es muy larga')
   if len(usuario.correo) != 28:
      errores.append('El correo debe tener 28 caracteres')
   elif validar_correo_alumnos(usuario.correo) == None:
      errores.append('Formato de correo incorrecto')
   return errores

def validar_matricula(matricula:str):
   """
   -Función que valida si una matrícula tiene el formato correcto utilizando una expresión regular
   -Argumento: La matrícula que ingresa el alumno en el formulario de registro
   -Return: Si hubo o no coincidencia
   """
   regex = re.compile('^S[0-9]{8}$')
   return (regex.match(matricula))

def validar_correo_alumnos(correo:str):
   """
   -Función que valida si un correo de alumno tiene el formato correcto utilizando una expresión regular
   -Argumento: El correo que ingresa el alumno en el formulario de registro
   -Return: Si hubo o no coincidencia
   """
   regex = re.compile('^zS[0-9]{8}@estudiantes.uv.mx$')
   return (regex.match(correo))

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
         ejercicioalumno = models.Ejerciciosalumnos(alumno=alumno,ejercicio=ejercicio, scriptEstudiante=script)
         ejercicioalumno.save()
         logging.info(f"El alumno {user} subió el ejercicio {ejercicio.titulo}")
         try:
            evaluacion_script(ejercicioalumno)
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
            return redirect('./listar_ejercicios_maestros')
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

def evaluacion_script(ejercicio_alumno:object):
   """
   -Función que empieza la evaluación del script que sube el alumno
      -Crea variables que guardan la ruta de los scripts que suben el maestro y el alumno, así como los campos de texto
      -Llama a la función 'creación_entorno_aislado' para que regrese las rutas donde se ejecutarán los scripts
      -Llama a la función 'conectarse_a_servidor' para que regrese el socket cliente con el que se conectará al servidor
      -Llama a la función 'enviar_datos_al_socket' para que el servidor reciba la ruta de los scripts de ejecución
      -Llama a la función 'recibir_variables_socket' para recibir el resultado de la evaluación de parámetros y comprobación de estado final
   -Argumento: Una instancia de 'Ejercicioalumno'
   """
   logging.info(f"Se está evaluando el ejercicio {ejercicio_alumno.ejercicio.titulo} del alumno {ejercicio_alumno.alumno.usuario}...")
   script_inicializacion = ('media/'+str(ejercicio_alumno.ejercicio.scriptInicial))
   script_comprobacion_parametros = ('media/'+str(ejercicio_alumno.ejercicio.scriptComprobacionP))
   script_estado_final = ('media/'+str(ejercicio_alumno.ejercicio.scriptComprobacionEF))
   script_estudiante = ('media/'+str(ejercicio_alumno.scriptEstudiante))
   entrada_prueba = ejercicio_alumno.ejercicio.entradaPrueba
   salida_esperada = ejercicio_alumno.ejercicio.salidaEsperada
   script_ini_seguro, script_com_param_seguro, script_est_final_seguro, script_estudiante_seguro, directorio_borrar = creacion_entorno_aislado(script_inicializacion, script_comprobacion_parametros, script_estado_final, script_estudiante)
   cliente_socket = conectarse_a_servidor()
   enviar_datos_al_socket(script_estudiante_seguro, script_ini_seguro, script_com_param_seguro, script_est_final_seguro, entrada_prueba, salida_esperada, cliente_socket)
   var_error_parametros, var_error_final = recibir_variables_socket(cliente_socket)
   ejercicio_alumno.resultadoFinal = var_error_final
   ejercicio_alumno.resultadoParametros = var_error_parametros
   ejercicio_alumno.save()
   os.system(f'rm -r {directorio_borrar}')

def conectarse_a_servidor():
   """
   -Función que crea un socket cliente y se conecta con el socket servidor
      -Si no se pudo crear la conexión termina el proceso
   -Return: Socket cliente
   """
   cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   try:
      cliente.connect(('127.0.0.1', int(1115)))
      logging.info("Conexión con el servidor del socket hecha")
      return cliente
   except ConnectionRefusedError:
      logging.exception("No se pudo realizar la conexión con el servidor del socket")
      exit(1)

def enviar_datos_al_socket(script_estudiante:str, script_inicializacion:str, script_comprobacion_parametros:str, script_estado_final:str, entrada_prueba:str, salida_esperada:str, cliente:socket):
   """
   -Función que envía la ruta de los script de alumno y maestro, y la entrada de prueba y salida esperada al socket servidor
      -Estas rutas están en un entorno limitado
      -Codifica el mensaje antes de enviarlo
   -Argumentos
      -Script del estudiante
      -Script de inicialización
      -Script de comprobación de estado final
      -Script de evaluación de parámetros
      -Entrada de prueba
      -Salida esperada
      -Socket cliente
   """
   mensaje = script_estudiante+'%##%'+script_inicializacion+'%##%'+script_comprobacion_parametros+'%##%'+script_estado_final+'%##%'+entrada_prueba+'%##%'+salida_esperada
   cliente.send(mensaje.encode('utf-8'))
   logging.info("Se enviaron los mensajes al servidor del socket")

def recibir_variables_socket(cliente:socket):
   """
   -Función que recibe los resultados de la evaluación del ejercicio ejecutado por el socket servidor
      -Decodifica el mensaje después de recibirlo
   -Argumento: Socket cliente
   -Returns:
      -Resultado de la evaluación de parámetros
      -Resultado de la comprobación de estado final
   """
   mensaje = cliente.recv(1024).decode('utf-8')
   partes = mensaje.split('%##%')
   var_error_parametros = partes[0]
   var_error_final = partes[1]
   logging.info("Se recibieron los mensajes del servidor del socket")
   return var_error_parametros, var_error_final

def creacion_entorno_aislado(script_inicializacion:str, script_comprobacion_parametros:str, script_estado_final:str, script_estudiante:str):
   """
   -Función que copia los archivos donde se guardaron inicialmente hacia un directorio que se ejecutará por un usuario limitado
      -Crea variables con las nuevas rutas en el entorno de ejecución
      -Les da permisos de ejecución a todos los archivos
   -Argumentos:
      -Script de inicialización
      -Script de evaluación de parámetros
      -Script de comprobación de estado final
      -Script del alumno
   -Return: Las variables con las nuevas rutas donde se ejecutarán los scripts
   """
   directorio_ejecucion = '/tmp/pruebas/'
   os.system(f'mkdir {directorio_ejecucion}')
   os.system(f'chown limitado {directorio_ejecucion}')
   os.system(f'cp {script_inicializacion} {directorio_ejecucion}; cp {script_comprobacion_parametros} {directorio_ejecucion}; cp {script_estado_final} {directorio_ejecucion}; cp {script_estudiante} {directorio_ejecucion}')
   archivo_script_ini = script_inicializacion.split('/')
   arcivo_script_param = script_comprobacion_parametros.split('/')
   archivo_script_estado = script_estado_final.split('/')
   archivo_script_alumno = script_estudiante.split('/')
   script_ini_seguro = (directorio_ejecucion+archivo_script_ini[2])
   script_com_param_seguro = (directorio_ejecucion+arcivo_script_param[2])
   script_est_final_seguro = (directorio_ejecucion+archivo_script_estado[2])
   script_estudiante_seguro = (directorio_ejecucion+archivo_script_alumno[2])
   print (script_ini_seguro)
   os.system(f'chmod +x {script_ini_seguro}')
   os.system(f'chmod +x {script_com_param_seguro}')
   os.system(f'chmod +x {script_est_final_seguro}')
   os.system(f'chmod +x {script_estudiante_seguro}')
   logging.info("Se copiaron los archivos a otro entorno para su ejecución")
   return script_ini_seguro, script_com_param_seguro, script_est_final_seguro, script_estudiante_seguro, directorio_ejecucion