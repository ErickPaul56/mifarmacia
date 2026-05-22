import os
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Configuración de la conexión a la base de datos en la nube (Aiven)
DB_CONFIG = {
    'host': 'mifarmacia-db-erickpaulrt-d549.j.aivencloud.com',
    'port': 24273,
    'user': 'avnadmin',
    'password': os.environ.get('DB_PASSWORD'),
    'database': 'defaultdb',
    'ssl_disabled': False
}

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def generar_respuesta_twiml(mensaje):
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Message>{mensaje}</Message>
    </Response>"""
    return twiml_response, 200, {'Content-Type': 'text/xml'}

# Ruta para que tu App Android registre usuarios
@app.route('/registrar', methods=['POST'])
def registrar():
    datos = request.json
    nombre = datos.get('nombre')
    telefono = datos.get('telefono')
    
    # Imprime en los logs para que veas qué recibe el servidor
    print(f"Recibido registro: {nombre} - {telefono}")
    
    conexion = obtener_conexion()
    if not conexion:
        return jsonify({"error": "No hay BD"}), 500
    
    try:
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO Usuario (nombre, telefono) VALUES (%s, %s)", (nombre, telefono))
        conexion.commit()
        cursor.close()
        conexion.close()
        return jsonify({"mensaje": "OK"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Ruta para el bot de WhatsApp
@app.route('/webhook', methods=['POST'])
def webhook():
    datos = request.values
    telefono_remitente = datos.get('From', '').replace('whatsapp:', '').strip()
    mensaje_recibido = datos.get('Body', '').strip().lower()
    
    conexion = obtener_conexion()
    if not conexion:
        return generar_respuesta_twiml("Lo siento, hay problemas técnicos. Intenta más tarde.")
        
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuario WHERE telefono = %s", (telefono_remitente,))
        usuario = cursor.fetchone()
        
        if not usuario:
            respuesta_bot = ("Hola. Veo que aún no te has registrado en nuestro sistema. "
                             "Por favor, descarga nuestra aplicación móvil \"MiFarmacIA\" "
                             "para darte de alta y agendar tu cita.")
        else:
            nombre = usuario['nombre']
            if "cita" in mensaje_recibido or "agendar" in mensaje_recibido:
                respuesta_bot = (f"Hola {nombre}, procedamos con la fecha de tu cita. "
                                 "Ingresa tu fecha ideal en formato: dd-mm-aa")
            else:
                respuesta_bot = (f"Hola {nombre}, bienvenido de nuevo a MiFarmacIA. "
                                 "¿Deseas agendar una cita médica o consultar sucursales?")
            
        cursor.close()
        conexion.close()
        return generar_respuesta_twiml(respuesta_bot)
    except Error as e:
        print(f"Error procesando webhook: {e}")
        return generar_respuesta_twiml("Hubo un error al procesar tu solicitud.")

if __name__ == '__main__':
    app.run(port=5000, debug=True)