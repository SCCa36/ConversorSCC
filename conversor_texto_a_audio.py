# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file, flash
from gtts import gTTS
from docx import Document
import PyPDF2
import os
import magic
from werkzeug.utils import secure_filename
from flask import after_this_request

#Creamos un directorio temporal donde guardar los archivos MP3.
os.makedirs('temp', exist_ok=True)
#Creamos una instancia de Flask.
aplicacion = Flask(__name__)
#Generamos una clave secreta aleatoria para los mensajes flash.
aplicacion.secret_key = os.urandom(24)
#Creamos la función encargada de verificar si el archivo es un archivo PDF válido.
def esUnArchivoPDFValido(archivo):
	try:
		lector_pdf = PyPDF2.PdfReader(archivo)
		return True
	except Exception:
		return False
#Creamos la función encargada de verificar si el archivo es un archivo de Word válido.
def esUnArchivoWordValido(archivo):
	try:
		Document(archivo)
		return True
	except Exception:
		return False
#Creamos la función encargada de convertir el contenido de un archivo de Word a texto.
def convertirWordATexto(archivo):
	documento = Document(archivo)
	texto_completo = []
	for parrafo in documento.paragraphs:
		texto_completo.append(parrafo.text)
	return '\n'.join(texto_completo)
#Creamos la función encargada de convertir el contenido de un archivo PDF a texto.
def convertirPDFATexto(archivo):
	lector_pdf = PyPDF2.PdfReader(archivo)
	texto_completo = []
	for pagina in lector_pdf.pages:
		texto_completo.append(pagina.extract_text())
	return '\n'.join(texto_completo)
#Creamos la ruta principal de la aplicación.
@aplicacion.route("/", methods=["GET", "POST"])
def index():
	if request.method == 'POST':
		archivo = request.files['archivo']
		extension_archivo = archivo.filename.split('.')[-1].lower()
		#Validamos la extensión.
		if extension_archivo not in ['docx', 'pdf']:
			flash('Sólo se permiten archivos .docx y .pdf.', "danger")
			return render_template('index.html')
		#Validamos el tipo de archivo.
		mime = magic.Magic(mime=True)
		mime_archivo = mime.from_buffer(archivo.read(1024))
		archivo.seek(0)
		if extension_archivo == 'pdf' and mime_archivo != 'application/pdf':
			flash("El archivo no es un archivo PDF válido.", "danger")
			return render_template('index.html')
		if extension_archivo == 'docx' and mime_archivo != 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
			flash("El archivo no es un archivo de Word válido.", "danger")
			return render_template('index.html')
		#Si el archivo es válido, lo procesamos.
		if extension_archivo == 'docx' and esUnArchivoWordValido(archivo):
			texto = convertirWordATexto(archivo)
		elif extension_archivo == 'pdf' and esUnArchivoPDFValido(archivo):
			texto = convertirPDFATexto(archivo)
		else:
			flash("El archivo está dañado o no es compatible.", "danger")
			return render_template('index.html')
		#Convertimos el texto a MP3.
		conversor = gTTS(texto, lang='es')
		nombre_original = os.path.splitext(secure_filename(archivo.filename))[0]
		nombre_archivo_MP3 = f'{nombre_original}.mp3'
		ruta_MP3 = os.path.join('temp', nombre_archivo_MP3)
		conversor.save(ruta_MP3)
		#Eliminamos el archivo MP3 después de que el usuario lo descargue.
		@after_this_request
		def eliminar_archivo(respuesta):
		    try:
		        os.remove(ruta_MP3)
		    except Exception as e:
		        print(f"Error al eliminar el archivo: {e}")
		    return respuesta
		return send_file(ruta_MP3, as_attachment=True)
	#Si el usuario es la primera vez que accede a la aplicación mostramos la página principal.
	return render_template('index.html')
#Ejecutamos la aplicación de Flask.
if __name__ == "__main__":
	aplicacion.run(debug=True)