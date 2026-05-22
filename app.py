import os
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Configuración de la conexión a la base de datos (Aiven)
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
        return conexion
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def generar_respuesta_twiml(mensaje):
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{mensaje}</Message></Response>', 200, {'Content-Type': 'text/xml'}

@app.route('/registrar', methods=['POST'])
def registrar():
    datos = request.json
    nombre = datos.get('nombre')
    telefono = datos.get('telefono')
    
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

@app.route('/webhook', methods=['POST'])
def webhook():
    datos = request.values
    telefono_remitente = datos.get('From', '').replace('whatsapp:', '').strip()
    telefono_sin_prefijo = telefono_remitente.replace('521', '')
    
    conexion = obtener_conexion()
    if not conexion:
        return generar_respuesta_twiml("Error técnico.")
        
    try:
        cursor = conexion.cursor(dictionary=True)
        # Búsqueda robusta
        query = "SELECT * FROM Usuario WHERE telefono = %s OR telefono = %s"
        cursor.execute(query, (telefono_remitente, telefono_sin_prefijo))
        usuario = cursor.fetchone()
        
        if not usuario:
            respuesta_bot = "Hola. No estás registrado. Usa la App 'MiFarmacIA'."
        else:
            respuesta_bot = f"Hola {usuario['nombre']}, bienvenido de nuevo."
            
        cursor.close()
        conexion.close()
        return generar_respuesta_twiml(respuesta_bot)
    except Exception as e:
        print(f"Error en webhook: {e}")
        return generar_respuesta_twiml("Hubo un error al procesar tu solicitud.")

if __name__ == '__main__':
    app.run(port=5000, debug=True)