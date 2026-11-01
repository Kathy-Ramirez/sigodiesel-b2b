from flask import Flask, jsonify
from sqlalchemy import text
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

from config import Config
from extensions import db, bcrypt

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Registrar los modelos para Flask-Migrate.
import models  # noqa: E402
from routes.auth import auth_bp  # noqa: E402
app.register_blueprint(auth_bp, url_prefix="/api/auth")

# usuarios trasportistas y despachadores
from routes.usuarios import usuarios_bp
app.register_blueprint(usuarios_bp, url_prefix="/api/usuarios")

# estaciones y empresas
from routes.empresas import empresas_bp
from routes.estaciones import estaciones_bp
app.register_blueprint(empresas_bp, url_prefix="/api/empresas")
app.register_blueprint(estaciones_bp, url_prefix="/api/estaciones")

# NUEVOS ENPOIND PARA VEHICLO Y TABLA ASIGNACION
from routes.vehiculos import vehiculos_bp
from routes.asignaciones import asignaciones_bp
app.register_blueprint(vehiculos_bp, url_prefix="/api/vehiculos")
app.register_blueprint(asignaciones_bp, url_prefix="/api/asignaciones")

# ENPOIND DE CUPO WNTIDAD
from routes.cupos import cupos_bp
app.register_blueprint(cupos_bp, url_prefix="/api/cupos")

# ENPIND DE TIQUED
from routes.tiquetes import tiquetes_bp
app.register_blueprint(tiquetes_bp, url_prefix="/api/tiquetes")

# ahora la taba despachos
from routes.despachos import despachos_bp
app.register_blueprint(despachos_bp, url_prefix="/api/despachos")

# vists para el trasportits 
from routes.transportistas import transportistas_bp
app.register_blueprint(transportistas_bp, url_prefix="/api/transportistas")

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "API de SIGODIESEL B2B funcionando",
    })


@app.get("/api/health/db")
def health_db():
    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return jsonify({
            "status": "ok",
            "database": "connected",
        }), 200

    except Exception:
        app.logger.exception("Error al conectar con PostgreSQL")
        return jsonify({
            "status": "error",
            "database": "unavailable",
        }), 503


if __name__ == "__main__":
    app.run(debug=True)