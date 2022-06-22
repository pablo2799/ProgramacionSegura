import socket
import sys
import threading
import subprocess

def funcion_ejecutar_inicializacion(script_inicializacion):
   chmod_inicializacion = ['chmod', '+x']
   chmod_inicializacion.append(script_inicializacion)
   chmod_inicializacion_salida = subprocess.Popen(chmod_inicializacion , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = chmod_inicializacion_salida.communicate()
   ejecutar_inicializacion  = []
   ejecutar_inicializacion.append(script_inicializacion)
   ejecutar_inicializacion_salida = subprocess.Popen(ejecutar_inicializacion , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = ejecutar_inicializacion_salida.communicate()

def funcion_ejecutar_comprobacion_parametros(script_comprobacion_parametros, script_estudiante, cliente):
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
   return var_error_parametros

def funcion_ejecutar_script_alumno(script_estudiante, entradas_prueba):
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

   return resultado

def funcion_ejecutar_estado_final(script_estado_final, salida_esperada, resultado, cliente):
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
   
   return var_error_final

def crear_socket_servidor():
    mi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mi_socket.bind(('', int(1115)))  # hace el bind en cualquier interfaz disponible
    return mi_socket
    
def ejecutar_scripts(cliente, mutex):
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

def escuchar(servidor, mutex):
   print("entro al escuchar")
   servidor.listen(2) # peticiones de conexion simultaneas
   while True:
      conn, addr = servidor.accept() # bloqueante, hasta que llegue una peticion
      hiloAtencion = threading.Thread(target=ejecutar_scripts, args=(conn, mutex)) # se crea un hilo de atención por cliente
      hiloAtencion.start()

if __name__ == '__main__':
    servidor = crear_socket_servidor()
    mutex = threading.Lock()
    escuchar(servidor, mutex)
    servidor.close()
