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
    'ssl_disabled': False # Aiven exige SSL de forma obligatoria
}

def obtener_conexion():
    """Establece una conexión con la base de datos MySQL en la nube."""
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

@app.route('/', methods=['GET'])
def inicio():
    """Ruta de prueba para verificar que el servidor está encendido."""
    return "Servidor Backend de MiFarmacIA operando con éxito en la nube.", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Punto de acceso que recibirá los mensajes de WhatsApp."""
    # Twilio envía los datos en formato Form URL Encoded
    datos = request.values
    
    # Extraemos el número de teléfono del remitente y el mensaje recibido
    telefono_remitente = datos.get('From', '').replace('whatsapp:', '').trim()
    mensaje_recibido = datos.get('Body', '').strip().lower()
    
    print(f"Mensaje recibido de {telefono_remitente}: {mensaje_recibido}")
    
    # Respuesta por defecto que armaremos usando la sintaxis de Twilio (TwiML)
    respuesta_bot = ""
    
    conexion = obtener_conexion()
    if conexion is None:
        respuesta_bot = "Lo siento, estamos experimentando problemas técnicos. Intenta más tarde."
        return generar_respuesta_twiml(respuesta_bot)
        
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # 1. Verificar si el usuario ya existe en la base de datos
        cursor.execute("SELECT * FROM Usuario WHERE telefono = %s", (telefono_remitente,))
        usuario = cursor.fetchone()
        
        if not usuario:
            # Si no existe, lo invitamos a usar la app de Android que programamos
            respuesta_bot = ("¡Hola! Bienvenido a MiFarmacIA. Notamos que aún no estás registrado. "
                             "Por favor, abre nuestra aplicación móvil oficial para darte de alta en unos segundos.")
        else:
            # Si el usuario ya existe, procesamos sus solicitudes
            nombre_usuario = usuario['nombre']
            
            if "cita" in mensaje_recibido or "agendar" in mensaje_recibido:
                respuesta_bot = f"Hola {nombre_usuario}, claro que sí. Por favor ingresa la fecha ideal para tu consulta en formato DD-MM-AAAA."
            elif "horario" in mensaje_recibido or "farmacia" in mensaje_recibido:
                respuesta_bot = "Nuestros consultorios atienden de Lunes a Domingo de 08:00 a 21:00 horas."
            else:
                respuesta_bot = f"Hola {nombre_usuario}, bienvenido de nuevo a MiFarmacIA. ¿En qué puedo ayudarte hoy?\n1. Agendar una cita médica\n2. Consultar horarios de sucursales"
                
        cursor.close()
        conexion.close()
        
    except Error as e:
        print(f"Error procesando el webhook: {e}")
        respuesta_bot = "Hubo un error al procesar tu solicitud. Por favor intenta de nuevo."

    return generar_respuesta_twiml(respuesta_bot)

def generar_respuesta_twiml(mensaje):
    """Genera la estructura XML exacta que Twilio necesita para responder en WhatsApp."""
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Message>{mensaje}</Message>
    </Response>"""
    return twiml_response, 200, {{'Content-Type': 'text/xml'}}

if __name__ == '__main__':
    # Ejecución local para pruebas iniciales
    app.run(port=5000, debug=True)