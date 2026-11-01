from datetime import timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from extensions import db, bcrypt
from models import Usuario, Rol
import secrets
from flask import current_app
from sqlalchemy.exc import IntegrityError


auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Debes proporcionar correo y contraseña",
        }), 400

    usuario = Usuario.query.filter_by(email=email).first()

    if (
        usuario is None
        or not usuario.activo
        or not bcrypt.check_password_hash(
            usuario.password_hash, password
        )
    ):
        return jsonify({
            "error": "Credenciales incorrectas o usuario inactivo",
        }), 401

    rol = db.session.get(Rol, usuario.id_rol)

    if rol is None:
        return jsonify({
            "error": "El usuario no tiene un rol válido",
        }), 403

    token = create_access_token(
        identity=str(usuario.id_usuario),
        additional_claims={
            "rol": rol.nombre_rol,
            "id_usuario": usuario.id_usuario,
            "id_estacion": usuario.id_estacion,
        },
        expires_delta=timedelta(minutes=30),
    )

    return jsonify({
        "mensaje": "Inicio de sesión correcto",
        "access_token": token,
        "token_type": "Bearer",
        "usuario": {
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "email": usuario.email,
            "rol": rol.nombre_rol,
        },
    }), 200


@auth_bp.get("/me")
@jwt_required()
def perfil_actual():
    usuario_id = get_jwt_identity()
    usuario = db.session.get(Usuario, int(usuario_id))

    if usuario is None or not usuario.activo:
        return jsonify({
            "error": "Usuario inexistente o inactivo",
        }), 401

    claims = get_jwt()

    return jsonify({
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "rol": claims.get("rol"),
        "activo": usuario.activo,
    }), 200

# @auth_bp.post("/initial-admin")
# def crear_administrador_inicial():

#     # Comprobar la clave temporal de inicialización.
#     clave_configurada = current_app.config.get(
#         "BOOTSTRAP_SETUP_KEY"
#     )

#     clave_recibida = request.headers.get("X-Setup-Key", "")

#     if (
#         not clave_configurada
#         or not secrets.compare_digest(
#             clave_recibida,
#             clave_configurada
#         )
#     ):
#         return jsonify({
#             "error": "No autorizado"
#         }), 401

#     data = request.get_json(silent=True) or {}

#     nombre = data.get("nombre", "").strip()
#     apellido = data.get("apellido", "").strip()
#     email = data.get("email", "").strip().lower()
#     password = data.get("password", "")

#     if not all([nombre, apellido, email, password]):
#         return jsonify({
#             "error": "Todos los campos son obligatorios"
#         }), 400

#     if len(password) < 12:
#         return jsonify({
#             "error": "La contraseña debe tener al menos 12 caracteres"
#         }), 400

#     # Impedir que se utilice este endpoint si ya existe un administrador.
#     rol_admin = Rol.query.filter_by(
#         nombre_rol="ADMINISTRADOR"
#     ).first()

#     if rol_admin:
#         existe_admin = Usuario.query.filter_by(
#             id_rol=rol_admin.id_rol
#         ).first()

#         if existe_admin:
#             return jsonify({
#                 "error": "Ya existe un administrador inicial"
#             }), 409

#     if Usuario.query.filter_by(email=email).first():
#         return jsonify({
#             "error": "El correo ya está registrado"
#         }), 409

#     try:
#         # Crear los tres roles si todavía no existen.
#         roles = [
#             "ADMINISTRADOR",
#             "TRANSPORTISTA",
#             "DESPACHADOR",
#         ]

#         for nombre_rol in roles:
#             existente = Rol.query.filter_by(
#                 nombre_rol=nombre_rol
#             ).first()

#             if existente is None:
#                 db.session.add(Rol(nombre_rol=nombre_rol))

#         db.session.flush()

#         rol_admin = Rol.query.filter_by(
#             nombre_rol="ADMINISTRADOR"
#         ).first()

#         administrador = Usuario(
#             id_rol=rol_admin.id_rol,
#             nombre=nombre,
#             apellido=apellido,
#             email=email,
#             password_hash=bcrypt.generate_password_hash(
#                 password
#             ).decode("utf-8"),
#             activo=True,
#         )

#         db.session.add(administrador)
#         db.session.commit()

#         return jsonify({
#             "mensaje": "Administrador inicial creado correctamente",
#             "usuario": {
#                 "id_usuario": administrador.id_usuario,
#                 "nombre": administrador.nombre,
#                 "apellido": administrador.apellido,
#                 "email": administrador.email,
#                 "rol": "ADMINISTRADOR",
#             }
#         }), 201

#     except IntegrityError:
#         db.session.rollback()
#         return jsonify({
#             "error": "No se pudo crear el administrador. "
#                      "Verifica que el correo no esté duplicado."
#         }), 409

#     except Exception:
#         db.session.rollback()
#         current_app.logger.exception(
#             "Error creando administrador inicial"
#         )
#         return jsonify({
#             "error": "Error interno al crear el administrador"
#         }), 500