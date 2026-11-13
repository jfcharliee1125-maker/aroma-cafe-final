import os
from datetime import datetime
from flask import Flask, jsonify, request, session, render_template
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
# Clave secreta necesaria para manejar las sesiones de usuario
app.secret_key = "tu_clave_secreta_super_segura"

CORS(app)

# Conexión directa a tu base de datos en MongoDB Atlas
client = MongoClient("mongodb://jfcharliee1125_db_user:bqt3ve2VARr-PjN@ac-fswlmxg-shard-00-00.yxxfzf9.mongodb.net:27017,ac-fswlmxg-shard-00-01.yxxfzf9.mongodb.net:27017,ac-fswlmxg-shard-00-02.yxxfzf9.mongodb.net:27017/aroma_cafe?ssl=true&replicaSet=atlas-7rnzw2-shard-0&authSource=admin&retryWrites=true&w=majority")
db = client["aroma_cafe"]
coleccion_pedidos = db["pedidos"]
coleccion_comentarios = db["comentarios"]
coleccion_promociones = db["promociones"]  # Colección para las promos dinámicas


# --- RUTAS PARA LAS VISTAS HTML PRINCIPALES ---

@app.route("/")
@app.route("/index.html")
def inicio():
    return render_template("index.html")

@app.route("/menu")
@app.route("/menu.html")
def menu():
    return render_template("menu.html")

@app.route("/ordenar")
@app.route("/ordenar.html")
def ordenar():
    return render_template("ordenar.html")

@app.route("/admin")
@app.route("/admin.html")
def admin():
    return render_template("admin.html")

@app.route("/contacto")
@app.route("/contacto.html")
def contacto():
    return render_template("contacto.html")

@app.route("/servicios")
@app.route("/servicios.html")
def servicios():
    return render_template("servicios.html")

@app.route("/galeria")
@app.route("/galeria.html")
def galeria():
    return render_template("galeria.html")

@app.route("/nosotros")
@app.route("/nosotros.html")
def nosotros():
    return render_template("nosotros.html")

@app.route("/ia")
def ia():
    return render_template("ia.html")


# --- RUTA DE AUTENTICACIÓN (LOGIN) ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    correo = data.get('correo')
    password = data.get('password')

    if correo == "amorycafe@gmail.com" and password == "lara2026":
        return jsonify({"exito": True, "rol": "admin", "mensaje": "Bienvenido Administrador"})
    elif correo == "matutino@gmail.com" and password == "matutino2026":
        return jsonify({"exito": True, "rol": "encargado", "turno": "Matutino", "mensaje": "Bienvenido Encargado Matutino"})
    elif correo == "vespertino@gmail.com" and password == "vespertino2026":
        return jsonify({"exito": True, "rol": "encargado", "turno": "Vespertino", "mensaje": "Bienvenido Encargado Vespertino"})
    elif correo == "marketing@gmail.com" and password == "market2026":
        return jsonify({"exito": True, "rol": "marketing", "mensaje": "Bienvenido al panel de marketing"})
    
    return jsonify({"exito": False, "mensaje": "Credenciales incorrectas"}), 401


# --- RUTAS DE PEDIDOS ---

@app.route("/api/guardar-pedido", methods=["POST"])
def guardar_pedido():
    datos = request.json
    if not datos:
        return jsonify({"error": "No se recibieron datos"}), 400

    datos["estado"] = "Pendiente"
    
    if "metodoPago" not in datos or not datos["metodoPago"]:
        datos["metodoPago"] = "Efectivo"

    coleccion_pedidos.insert_one(datos)
    return jsonify({"mensaje": "¡Pedido guardado con éxito!"}), 200

@app.route("/api/pedidos", methods=["GET"])
def obtener_pedidos():
    pedidos = list(coleccion_pedidos.find({}, {"_id": False}))
    return jsonify(pedidos)

@app.route("/api/pedidos/<folio>", methods=["PUT"])
def actualizar_estado(folio):
    datos = request.json
    nuevo_estado = datos.get("estado")
    
    if not nuevo_estado:
        return jsonify({"error": "No se proporcionó el nuevo estado"}), 400

    resultado = coleccion_pedidos.update_one(
        {"folio": folio},
        {"$set": {"estado": nuevo_estado}}
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Pedido no encontrado"}), 404

    return jsonify({"mensaje": "Estado actualizado con éxito"}), 200

@app.route("/api/pedidos/<folio>/pago", methods=["PUT"])
def actualizar_pago(folio):
    datos = request.json
    nuevo_pago = datos.get("metodoPago")
    
    if not nuevo_pago:
        return jsonify({"error": "No se proporcionó el método de pago"}), 400

    resultado = coleccion_pedidos.update_one(
        {"folio": folio},
        {"$set": {"metodoPago": nuevo_pago}}
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Pedido no encontrado"}), 404

    return jsonify({"mensaje": "Método de pago actualizado con éxito"}), 200

@app.route("/api/pedidos/completados", methods=["DELETE"])
def eliminar_completados():
    resultado = coleccion_pedidos.delete_many({"estado": {"$regex": "^completado$", "$options": "i"}})
    return jsonify({"mensaje": f"Se eliminaron {resultado.deleted_count} pedidos completados."}), 200


# --- RUTAS DE COMENTARIOS Y CALIFICACIONES ---

@app.route("/api/comentarios", methods=["POST"])
def guardar_comentario():
    datos = request.json
    if not datos or "comentario" not in datos:
        return jsonify({"error": "No se recibió el comentario"}), 400

    correo_usuario = datos.get("correo") or session.get("user_email") or "usuario desconocido"

    nuevo_comentario = {
        "correo": correo_usuario,
        "comentario": datos.get("comentario"),
        "calificacion": int(datos.get("calificacion", 5)),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    coleccion_comentarios.insert_one(nuevo_comentario)
    return jsonify({"mensaje": "¡Comentario guardado con éxito!"}), 200

@app.route("/api/comentarios", methods=["GET"])
def obtener_comentarios():
    comentarios = list(coleccion_comentarios.find().sort("_id", -1))
    for c in comentarios:
        c["_id"] = str(c["_id"])
    return jsonify(comentarios)

@app.route("/api/comentarios/<id>", methods=["DELETE"])
def eliminar_comentario(id):
    try:
        resultado = coleccion_comentarios.delete_one({"_id": ObjectId(id)})
        if resultado.deleted_count == 0:
            return jsonify({"error": "Comentario no encontrado"}), 404
        return jsonify({"mensaje": "Comentario eliminado con éxito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/comentarios/eliminar-multiples", methods=["POST"])
def eliminar_multiples_comentarios():
    datos = request.json
    ids = datos.get("ids", [])
    
    if not ids:
        return jsonify({"error": "No se seleccionaron comentarios"}), 400

    try:
        object_ids = [ObjectId(id_str) for id_str in ids]
        resultado = coleccion_comentarios.delete_many({"_id": {"$in": object_ids}})
        return jsonify({"mensaje": f"Se eliminaron {resultado.deleted_count} comentarios correctamente."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/comentarios/<id>/responder", methods=["POST"])
def responder_comentario(id):
    datos = request.json
    respuesta_texto = datos.get("respuesta")
    
    if not respuesta_texto:
        return jsonify({"error": "La respuesta no puede estar vacía"}), 400

    try:
        resultado = coleccion_comentarios.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"respuesta": respuesta_texto}}
        )
        if resultado.matched_count == 0:
            return jsonify({"error": "Comentario no encontrado"}), 404
        return jsonify({"mensaje": "Respuesta guardada con éxito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# --- RUTAS DE PROMOCIONES DINÁMICAS ---

@app.route("/api/promociones", methods=["GET"])
def obtener_promociones():
    promociones = list(coleccion_promociones.find())
    for p in promociones:
        p["_id"] = str(p["_id"])
    return jsonify(promociones)

@app.route("/api/promociones", methods=["POST"])
def guardar_promocion():
    datos = request.json
    if not datos:
        return jsonify({"error": "No se recibieron datos de la promoción"}), 400

    resultado = coleccion_promociones.insert_one(datos)
    return jsonify({"mensaje": "¡Promoción guardada en MongoDB con éxito!", "id": str(resultado.inserted_id)}), 200

@app.route("/api/promociones/<id>", methods=["DELETE"])
def eliminar_promocion(id):
    try:
        resultado = coleccion_promociones.delete_one({"_id": ObjectId(id)})
        if resultado.deleted_count == 0:
            return jsonify({"error": "Promoción no encontrada"}), 404
        return jsonify({"mensaje": "Promoción eliminada con éxito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# --- RUTA COMODÍN PARA CUALQUIER OTRA VISTA HTML ADICIONAL ---
@app.route('/<path:pagina>')
def cargar_pagina_generica(pagina):
    if not pagina.endswith('.html'):
        pagina += '.html'
    try:
        return render_template(pagina)
    except Exception:
        return render_template('index.html')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)