from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import requests
import os
#____________________________________________________________________________________
#cargar variables de entorno
load_dotenv()
#____________________________________________________________________________________
app = Flask(__name__)

#Coniguración de la base de datos SQLITE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Modelo de la tabla log
class Log(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default = datetime.utcnow)
    texto = db.Column(db.TEXT)

#Crear la tabla si no existe
with app.app_context():
    db.create_all()

    #prueba1 = Log(texto = 'Mensaje de prueba 1') 
    #prueba2 = Log(texto = 'Mensaje de prueba 2') 

    #db.session.add(prueba1)
    #db.session.add(prueba2)
    #db.session.commit()

#funcion para ordenar los registros por fecha y hora
def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)


#Función información a la base de datos
def agregar_mensajes_log(texto):
    #gurardar mensajes en la base de datos
    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

@app.route('/')

def index():
    #obtener todos los registros de la base de datos
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html',registros = registros_ordenados)

#funcion para obtener el acceso de token desde refresh token
def get_access_token():
    url= "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "refresh_token": os.getenv("ZOHO_REFRESH_TOKEN"),
        "client_id": os.getenv("ZOHO_CLIENT_ID"),
        "client_secret": os.getenv("ZOHO_CLIENT_SECRET"),
        "grant_type": "refresh_token"
    }

    response = requests.post(url,params=params)
    data = response.json()
    return f"DEBUG: {data}"

    #print(f"Token response: {data}")

    #if "access_token" in data:
    #    return data["access_token"]
    #else:
    #    print(f"Error al obtener token: {data}")
    #    return None
# ─────────────────────────────────────────────────────────────

@app.route('/debug-token')
def debug_token():
    return get_access_token()
    #access_token = get_access_token()
    #return f"Access token (si existe): {access_token}"

# ─────────────────────────────────────────────────────────────
# OPCIONAL: Obtener refresh_token desde el code (una vez)
@app.route('/obtener-refresh-token')
def get_refresh_token_once():
    code = request.args.get('code')
    if not code:
        return "❌ Debes pasar el parámetro ?code=XXXXX"

    url = "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "code": code,
        "client_id": os.getenv("ZOHO_CLIENT_ID"),
        "client_secret": os.getenv("ZOHO_CLIENT_SECRET"),
        "redirect_uri": os.getenv("ZOHO_REDIRECT_URI"),
        "grant_type": "authorization_code"
    }

    response = requests.post(url, params=params)
    data = response.json()
    return data  # Muestra access_token y refresh_token

# ─────────────────────────────────────────────────────────────
# Ruta de prueba para enviar Lead a Zoho
@app.route('/enviar-a-zoho')

def enviar_a_zoho():
    access_token = get_access_token()

    if not access_token:
        return "Error al obtener access_token"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "data": [
            {
                "First_Name": "César",
                "Last_Name": "Chavarriaga",
                "Email": "cesar@example.com",
                "Mobile": "3000000000",
                "Origen": "WhatsApp"
            }
        ],
        "duplicate_check_fields": ["Email"]
    }

    url = os.getenv("ZOHO_API_URL") + "/upsert"

    response = requests.post(url, headers=headers, json=payload)
    print("Access token usado en envío:", access_token)


    try:
        data = response.json()
    except Exception as e:
        data = {"error": "No JSON response", "raw": response.text}

    if response.status_code in [200, 201]:
        agregar_mensajes_log("✅ Lead enviado correctamente")
        return "✅ Lead enviado correctamente"
    else:
        agregar_mensajes_log("❌ Error al enviar Lead: " + str(data))
        return f"❌ Error al enviar Lead: {data}", 500

# Ruta para recibir el código OAuth de Zoho
@app.route('/oauth2callback')
def oauth_callback():
    code = request.args.get('code')
    if code:
        return f"Código recibido correctamente: {code}"
    else:
        return "No se recibió ningún código."

if __name__=='__main__':
    app.run(host='0.0.0.0',port=80,debug=True)