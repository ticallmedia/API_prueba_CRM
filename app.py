from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import requests
import os
#________________________________________________________________________________________
# Cargar variables de entorno desde .env
load_dotenv()
#________________________________________________________________________________________
app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar base de datos
db = SQLAlchemy(app)

# Modelo de tabla para logs
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto = db.Column(db.TEXT)

# Crear la tabla si no existe
with app.app_context():
    db.create_all()

# Funciones auxiliares

def agregar_mensajes_log(texto):
    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)

def get_access_token():
    url = "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "refresh_token": os.getenv("ZOHO_REFRESH_TOKEN"),
        "client_id": os.getenv("ZOHO_CLIENT_ID"),
        "client_secret": os.getenv("ZOHO_CLIENT_SECRET"),
        "grant_type": "refresh_token"
    }
    response = requests.post(url, params=params)
    data = response.json()
    print("DEBUG:", data)
    if "access_token" in data:
        return data["access_token"]
    else:
        return None
#________________________________________________________________________________________
# Rutas principales

@app.route('/')
def index():
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html', registros=registros_ordenados)
#________________________________________________________________________________________
@app.route('/enviar-a-zoho')
def enviar_a_zoho():
    access_token = get_access_token()
    if not access_token:
        return "❌ Error al obtener access_token"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "data": [
            {
                "First_Name": "Joaquin",
                "Last_Name": "Chavarriaga Muñoz",
                "Email": "joaquin@example.com",
                "Mobile": "3100000000",
                "Origen": "WhatsApp"
            }
        ],
        "duplicate_check_fields": ["Email"]
    }

    url = os.getenv("ZOHO_API_URL") + "/upsert"
    response = requests.post(url, headers=headers, json=payload)

    try:
        data = response.json()
    except:
        data = {"error": "Respuesta no válida de Zoho", "raw": response.text}

    if response.status_code in [200, 201]:
        agregar_mensajes_log("✅ Lead enviado correctamente")
        return "✅ Lead enviado correctamente"
    else:
        agregar_mensajes_log("❌ Error al enviar Lead: " + str(data))
        return f"❌ Error al enviar Lead: {data}", 500
#________________________________________________________________________________________
@app.route('/oauth2callback')
def oauth_callback():
    code = request.args.get('code')
    if code:
        return f"Código recibido correctamente: {code}"
    return "No se recibió ningún código."
#________________________________________________________________________________________
@app.route('/debug-token')
def debug_token():
    token = get_access_token()
    return f"Access token (si existe): {token}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
#________________________________________________________________________________________
