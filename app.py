import os
from flask import Flask, request
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

@app.route('/webhook', methods=['POST'])
def webhook():
    datos = request.values
    telefono_remitente = datos.get('From', '').replace('whatsapp:', '').strip()
    mensaje_recibido = datos.get('Body', '').strip().lower()
    
    conexion = obtener_conexion()
    if not conexion:
        return generar_respuesta_twiml("Lo siento, estamos experimentando problemas técnicos. Intenta más tarde.")
        
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuario WHERE telefono = %s", (telefono_remitente,))
        usuario = cursor.fetchone()
        
        if not usuario:
            # Respuesta para usuario nuevo
            respuesta_bot = ("Hola. Veo que aún no te has registrado en nuestro sistema. "
                             "Por favor, descarga nuestra aplicación móvil \"Farmacia Bot\" "
                             "para darte de alta y agendar tu cita.")
        else:
            # Flujo para usuario registrado
            nombre = usuario['nombre']
            
            if "cita" in mensaje_recibido or "agendar" in mensaje_recibido:
                respuesta_bot = (f"Hola {nombre}, procedamos con la fecha de tu cita. "
                                 "Ingresa tu fecha ideal para consultar disponibilidad "
                                 "en el siguiente formato: dd-mm-aa")
            elif any(char.isdigit() for char in mensaje_recibido) and "-" in mensaje_recibido:
                respuesta_bot = ("Se ha encontrado disponibilidad en al menos 4 farmacias cerca de ti. "
                                 "Por favor ingresa tu horario más conveniente en formato 24 horas (Ej: 16:30).")
            elif "horario" in mensaje_recibido or "farmacia" in mensaje_recibido:
                respuesta_bot = "Nuestros consultorios atienden de Lunes a Domingo de 08:00 a 21:00 horas."
            else:
                respuesta_bot = (f"Hola {nombre}, bienvenido de nuevo a MiFarmacIA. "
                                 "¿Deseas agendar una cita médica o consultar sucursales?")
            
        cursor.close()
        conexion.close()
        return generar_respuesta_twiml(respuesta_bot)

    except Error as e:
        print(f"Error procesando el webhook: {e}")
        return generar_respuesta_twiml("Hubo un error al procesar tu solicitud. Por favor intenta de nuevo.")

if __name__ == '__main__':
    app.run(port=5000, debug=True)