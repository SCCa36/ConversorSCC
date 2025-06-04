# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
import os
import time
import threading
from werkzeug.utils import secure_filename
from docx import Document
from gtts import gTTS
import textract
import fitz
from werkzeug.exceptions import RequestEntityTooLarge

#Creamos una instancia de Flask
aplicacion = Flask(__name__)
#Creamos la clave secreta para la aplicación.
aplicacion.secret_key = os.urandom(24)
#Indicamos cuál va a ser el directorio donde vamos a guardar los archivos de audio.
CARPETA_SUBIDAS = 'static/audio'
#Indicamos el tamaño máximo permitido.
TAMANO_MAXIMO_PERMITIDO = 20 * 1024 * 1024
#En caso de que no exista, creamos el directorio donde vamos a guardar los archivos de audio.
os.makedirs(CARPETA_SUBIDAS, exist_ok=True)
#Configuramoos el directorio donde vamos a guardar los archivos de audio y el tamaño máximo del archivo.
aplicacion.config['UPLOAD_FOLDER'] = CARPETA_SUBIDAS
aplicacion.config['MAX_CONTENT_LENGTH'] = TAMANO_MAXIMO_PERMITIDO
#Creamos la función encargada de leer los documentos.
def leerDocumento(ruta_archivo):
	#Obtenemos la extensión del archivo subido por el usuario.
	extension = os.path.splitext(ruta_archivo)[1].lower()
	#En caso de que la extensión sea una de las extensiones permitidas (.doc, .docx y .pdf), extraemos el texto del archivo.
	if extension == '.docx':
		documento = Document(ruta_archivo)
		return '\n'.join([parrafo.text for parrafo in documento.paragraphs])
	elif extension == '.doc':
		texto = textract.process(ruta_archivo).decode('utf-8')
		return texto
	elif extension == '.pdf':
		texto = ""
		with fitz.open(ruta_archivo) as documento:
			for pagina in documento:
				texto += pagina.get_text()
		return texto
	else:
		#En caso de que la extensión no sea ninguna de las permitidas, lanzamos un mensaje de error.
		raise ValueError("\nEl tipo de archivo no es compatible.")
#Controlamos que el archivo subido por el usuario no sobrepase los 20 MB.
@aplicacion.errorhandler(RequestEntityTooLarge)
def archivoDemasiadoLargo():
	flash("El archivo excede el tamaño máximo permitido (20 MB).", "danger")
	return redirect('/')
#Creamos la función encargada de eliminar los archivos una vez haya pasado una hora.
def eliminarArchivosAntiguos(directorio, tiempo_maximo=3600):
	while True:
		ahora = time.time()
		for archivo in os.listdir(directorio):
			ruta = os.path.join(directorio, archivo)
			if os.path.isfile(ruta):
				#Si ha pasado una hora, eliminamos los archivos.
				if ahora - os.path.getmtime(ruta) > tiempo_maximo:
					os.remove(ruta)
		#Hacemos que el proceso se repita cada 10 minutos.
		time.sleep(600)
#Lanzamos el hilo encargado de eliminar todos los archivos en segundo plano.
threading.Thread(target=eliminarArchivosAntiguos, args=(CARPETA_SUBIDAS,), daemon=True).start()
#Creamos la única ruta de la aplicación.
@aplicacion.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		if 'archivo' not in request.files:
			flash("No se ha enviado ningún archivo.", "danger")
			return redirect(request.url)
		archivo = request.files['archivo']
		if archivo and archivo.filename.lower().emdswith(('.doc', '.docx', '.pdf')):
			nombre_archivo = secure_filename(archivo.filename)
			ruta = os.path.join(CARPETA_SUBIDAS, nombre_archivo)
			archivo.save(ruta)
			try:
				texto = leerDocumento(ruta)
				if not texto.strip():
					flash("El documento está vacío.", "warning")
					return redirect('/')
				tts = gTTS(text=texto, lang='es')
				nombre_archivo_audio = nombre_archivo.rsplit('.', 1)[0] + '.mp3'
				ruta_archivo_audio = os.path.join(CARPETA_SUBIDAS, nombre_archivo_audio)
				tts.save(ruta_archivo_audio)
				return render_template('index.html', archivo_audio=nombre_archivo_audio)
			except Exception as e:
				flash(f"Ocurrió un error: {str(e)}.", "danger")
				return redirect('/')
		else:
			flash("Sólo se permiten archivos de Word (.doc y .docx) y PDF (.pdf).", "danger")
			return redirect('/')
	return render_template('index.html', archivo_audio=None)
#Ejecutamos la aplicación de Flask.
if __name__ == "__main__":
	aplicacion.run(debug=True)