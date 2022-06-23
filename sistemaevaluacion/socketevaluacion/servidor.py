import socket
import threading
import subprocess
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                     datefmt='%d-%b-%y %H:%M:%S',
                     level=logging.INFO,
                     filename='logs/registro-eventos.log',
                     filemode='a'
)

def funcion_ejecutar_inicializacion(script_inicializacion):
   """
   -Función para ejercutar el script de inicializacion del ejercicio
   -Con la herramienta subprocess se ejecuta el script de inicializacion sin recuperar salidas
   -Argumento: la ruta del script de inicializacion
   -Return: No regresa nada
   """
   logging.info("Inició ejecutar la script_inicializacion")
   chmod_inicializacion = ['chmod', '+x']
   chmod_inicializacion.append(script_inicializacion)
   chmod_inicializacion_salida = subprocess.Popen(chmod_inicializacion , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = chmod_inicializacion_salida.communicate()
   ejecutar_inicializacion  = []
   ejecutar_inicializacion.append(script_inicializacion)
   ejecutar_inicializacion_salida = subprocess.Popen(ejecutar_inicializacion , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = ejecutar_inicializacion_salida.communicate()
   logging.info("Terminó de ejecutar la script_inicializacion")

def funcion_ejecutar_comprobacion_parametros(script_comprobacion_parametros, script_estudiante, cliente):
   """
   -Función para ejercutar el script de comprobacion de parametros
   -Con la herramienta subprocess se ejecuta el script de comprobacion de parametros para determinar si el script del
    estudiante tiene validaciones adecuadas mediante la ejecucion del script del estudiante.
   -Argumento: la ruta del ejercicio del script de comprobacion de parametros y del script del estudiante.
   -Return: Regresa 0 o un 1 dependiendo si la comprobacion de parametros tuvo exito o no.
   """
   logging.info("Ejecutar la comprobacion parametros")
   var_error_parametros=0
   chmod_parametros  = ['chmod', '+x']
   chmod_parametros.append(script_comprobacion_parametros)
   chmod_parametros_salida = subprocess.Popen(chmod_parametros , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = chmod_parametros_salida.communicate()
   #----------------------------------------------------------------------------------------------------------------------------------
   ejecutar_validar_parametros  = []
   ejecutar_validar_parametros.append(script_comprobacion_parametros)
   ejecutar_validar_parametros.append(script_estudiante)
   ejecutar_validar_parametros_salida = subprocess.Popen(ejecutar_validar_parametros , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = ejecutar_validar_parametros_salida.communicate()
   var_error_parametros = ejecutar_validar_parametros_salida.returncode
   logging.info("Terminó de ejecutar la comprobacion parametros")
   return var_error_parametros

def funcion_ejecutar_script_alumno(script_estudiante, entradas_prueba):
   """
   -Función para ejercutar el script del estudiante
   -Con la herramienta subprocess se ejecuta el script del estudiante para llevar a cabo lo que requiere el ejercicio, se verifica cuantas
    entradas de prueba tiene mediante un if, si tiene varias se hace un split para dividirlas, despues se ejecuta el script del estudiante
    con la o las entradas de prueba y se obtiene la salida stdout del ejercio si tiene alguna y la devuelve a la funcion de ejecutar scripts.
   -Argumento: la ruta del ejercicio del script del estudiante y las entradas de prueba.
   -Return: Regresa la salida estandar del script del estudiante y en caso de que no exista se regresa la variable vacia.
   """
   logging.info("Inició ejecutar el script del estudiante")
   cont=0
   cont_var_while=0
   resultado=""
   num_variables=1
   variable_prueba=entradas_prueba
   var_una_entrada=0
   #----------------------------------------------------------------------------------------------------------------------------------
   chmod_estudiante  = ['chmod', '+x']
   chmod_estudiante.append(script_estudiante)
   chmod_estudiante_salida = subprocess.Popen(chmod_estudiante , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = chmod_estudiante_salida.communicate()
   #----------------------------------------------------------------------------------------------------------------------------------
   ejecutar_script_estudiante  = []
   ejecutar_script_estudiante.append(script_estudiante)
   for i in entradas_prueba:
      if i == ',':
         cont += 1

   if cont >= 1:
      var_una_entrada=1
      variables=entradas_prueba.split(',')
      num_variables=len(variables)

   if var_una_entrada == 0:
      ejecutar_script_estudiante.append(variable_prueba)
      print("La entrada de prueba es: ",variable_prueba)
   else:
      while num_variables >= 1:
         ejecutar_script_estudiante.append(variables[cont_var_while])
         cont_var_while=cont_var_while+1
         num_variables=num_variables-1

   ejecutar_script_estudiante_salida = subprocess.Popen(ejecutar_script_estudiante , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = ejecutar_script_estudiante_salida.communicate()
   error = stderr.decode('utf-8')
   stdout = stdout.decode('utf-8')
   #----------------------------------------------------------------------------------------------------------------------------------
   if len(stdout) != 0:
      partes = stdout.split('\n')
      resultado_lista = partes[:-1]
      resultado = str(",".join(partes[:-1]))
   logging.info("Terminó de ejecutar el script del estudiante")

   return resultado

def funcion_ejecutar_estado_final(script_estado_final, salida_esperada, resultado, cliente):
   """
   -Función para ejercutar el script de estado final
   -Con la herramienta subprocess se ejecuta el script de estado final, verifica que el script del estudiante haya
    realizado lo que se pidio en el ejercicio, en caso de que haya salida esperada se compara con el resultado en el script
    de estado final.
   -Argumento: la ruta del ejercicio del script de estado final, la salida esperada y el resultado el script del estudiante.
   -Return: Regresa 0 o un 1 dependiendo de si realizo lo que pide el ejercicio.
   """
   logging.info("Inicio la comprobacion de estado final")
   chmod_estadoFinal  = ['chmod', '+x']
   chmod_estadoFinal.append(script_estado_final)
   chmod_estadoFinal_salida = subprocess.Popen(chmod_estadoFinal , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = chmod_estadoFinal_salida.communicate()
   if len(salida_esperada) == 0: 
      ejecutar_estadoFinal  = []
      ejecutar_estadoFinal.append(script_estado_final)
      ejecutar_estadoFinal_salida = subprocess.Popen(ejecutar_estadoFinal , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      stdout, stderr = ejecutar_estadoFinal_salida.communicate()
      var_error_final = ejecutar_estadoFinal_salida.returncode
      print(var_error_final)
   else:
      ejecutar_estadoFinal  = []
      ejecutar_estadoFinal.append(script_estado_final)
      ejecutar_estadoFinal.append(salida_esperada)
      ejecutar_estadoFinal.append(resultado)
      ejecutar_estadoFinal_salida = subprocess.Popen(ejecutar_estadoFinal , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      stdout, stderr = ejecutar_estadoFinal_salida.communicate()
      var_error_final = ejecutar_estadoFinal_salida.returncode
   logging.info("Termino la comprobacion de estado final")
   return var_error_final

def crear_socket_servidor():
   """
   -Función para crear el servidor del socket
   -Se crea el socket para las pruebas en cualquier interfas disponible y definiendo el puerto manualmente.
   -Argumento: ninguno
   -Return: Regresa el socket para las pruebas
   """
   mi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   mi_socket.bind(('', int(1117)))  # hace el bind en cualquier interfaz disponible
   logging.info("Se creó el socket servidor")
   return mi_socket
    
def ejecutar_scripts(cliente, mutex):
   """
   -Función ejecutar scrips
   -Se reciben los datos del cliente del socket que esta en las views del sistemaEvaluacion, se dividen los datos para poder
    usarlos mediante un split, se mandan las rutas de los scripts y los parametros para evaluar el script, se reciben las variables
    que regresan las funciones para poder definir si tuvo exito o no en las evaluaciones, se definen las variables con "exito" o
    "fallo" y al final se concatenan las varibles y se envian al cliente.
   -Argumento: el cliente del socket
   -Return
   """
   logging.info("Entró a la ejecucion de los scripts")
   print("entro al ejecutar_scripts")
   mensaje = cliente.recv(1024).decode('utf-8')
   partes = mensaje.split('%##%')
   script_estudiante = partes[0]
   script_inicializacion = partes[1]
   script_comprobacion_parametros = partes[2]
   script_estado_final = partes[3]
   entrada_prueba = partes[4]
   salida_esperada = partes[5]
   funcion_ejecutar_inicializacion(script_inicializacion)
   var_error_parametros = funcion_ejecutar_comprobacion_parametros(script_comprobacion_parametros, script_estudiante, cliente)
   resultado = funcion_ejecutar_script_alumno(script_estudiante, entrada_prueba)
   var_error_final = funcion_ejecutar_estado_final(script_estado_final, salida_esperada, resultado, cliente)
   print("--------------------------------------------")
   print(var_error_parametros)
   print(var_error_final)
   print("--------------------------------------------")
   if var_error_final == 0:
      var_error_final="exito";
   else:
      var_error_final="fallo";

   if var_error_parametros == 0:
      var_error_parametros="exito";
   else:
      var_error_parametros="fallo";

   mensaje_variables = var_error_parametros+'%##%'+var_error_final
   cliente.send(mensaje_variables.encode('utf-8'))
   logging.info("Termino de ejecutar los scripts")
   logging.info("Envió las variables al cliente")

def escuchar(servidor, mutex):
   """
   -Función para escuchar las conexiones al servidor atendiendo mediante hilos.
   -Hace que el servidor escuche peticiones y cuando llega una la manda a un hilo de atencion.
   -Argumento: El servidor del socket
   -Return: Regresa el cliente que se conecto mediante el hilo.
   """
   print("entro al escuchar")
   logging.info("Entro a escuchar en los hilos de hiloAtencion")
   servidor.listen(2) # peticiones de conexion simultaneas
   while True:
      conn, addr = servidor.accept() # bloqueante, hasta que llegue una peticion
      hiloAtencion = threading.Thread(target=ejecutar_scripts, args=(conn, mutex)) # se crea un hilo de atención por cliente
      hiloAtencion.start()

if __name__ == '__main__':
   """
   -Función principal 
   -Llama a las demas funciones para crear el socket, crear el hilo de atencion y escuchar las peticiones de los clientes.
   -Argumento: No recibe parametros
   -Return: Ninguno
   """
   logging.info("Inicio el programa del servidor socket")
   servidor = crear_socket_servidor()
   mutex = threading.Lock()
   escuchar(servidor, mutex)
   servidor.close()
