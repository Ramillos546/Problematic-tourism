import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from twilio.rest import Client
from dotenv import load_dotenv

# Configuración inicial
load_dotenv()
app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

DB_PATH = "ondera.db" # Asegúrense de correr database.py primero para crear esto

# Configuración de Twilio (Las credenciales van en su archivo .env)
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# ==========================================
# RUTA 1: RECEPCIÓN DEL SMS (LA IA SOLO SUGIERE, NO ENVÍA)
# ==========================================
@app.route("/sms", methods=["POST"])
def recibir_sms():
    mensaje_turista = request.form.get("Body", "")
    remitente = request.form.get("From", "")
    
    print(f"📩 SMS recibido de {remitente}: {mensaje_turista}")
    
    # 1. Aquí su compañero de IA conecta los modelos
    # intencion = clasificar_intencion(mensaje_turista)
    # mensaje_traducido = traducir(mensaje_turista)
    
    # Simulamos la IA por ahora para que el equipo pueda seguir trabajando
    intencion_sugerida = "reservar" 
    traduccion_sugerida = "Habari, nataka kuweka tour..." # Traducción al swahili
    respuesta_sugerida = "Asante! Noor atakupiga simu hivi karibuni." # Lo que Noor debería responder
    
    # 2. GUARDAR EN BASE DE DATOS COMO "PENDIENTE" (Esto cumple la regla del Hackathon)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reservas (telefono_turista, mensaje_original, mensaje_traducido, intencion, estado)
        VALUES (?, ?, ?, ?, 'pendiente')
    """, (remitente, mensaje_turista, respuesta_sugerida, intencion_sugerida))
    conn.commit()
    conn.close()
    
    # 3. Retornamos OK a Twilio para que no dé error, pero NO enviamos SMS.
    return "OK", 200

# ==========================================
# RUTA 2: EL BOTÓN DE NOOR (HUMAN-IN-THE-LOOP)
# ==========================================
@app.route("/api/aprobar_sms", methods=["POST"])
def aprobar_sms():
    # El frontend llama a esta ruta cuando Noor presiona "Aprobar y Enviar"
    data = request.json
    reserva_id = data["id"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT telefono_turista, mensaje_traducido FROM reservas WHERE id = ?", (reserva_id,))
    reserva = cursor.fetchone()
    
    if reserva:
        remitente = reserva[0]
        respuesta_final = reserva[1]
        
        # AHORA SÍ enviamos el mensaje porque Noor lo aprobó
        try:
            twilio_client.messages.create(
                to=remitente,
                from_=TWILIO_NUMBER,
                body=respuesta_final
            )
            # Actualizamos el estado a enviado
            cursor.execute("UPDATE reservas SET estado = 'enviado' WHERE id = ?", (reserva_id,))
            conn.commit()
            status = "✅ SMS enviado por Noor"
        except Exception as e:
            status = f"❌ Error enviando SMS: {e}"
            # Aquí entraría la lógica de Store-and-forward si no hay señal
            
    conn.close()
    return jsonify({"status": status})

if __name__ == "__main__":
    print("🚀 Servidor de Ondera Connect iniciado en http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
