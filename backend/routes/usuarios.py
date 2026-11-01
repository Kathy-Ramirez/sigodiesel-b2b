from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email, EmailNotValidError

from extensions import db, bcrypt
from models import Usuario, Rol, Empresa, Estacion


usuarios_bp = Blueprint("usuarios", __name__)


# --------------------------------------------------
# SEGURIDAD: SOLO ADMINISTRADOR
# --------------------------------------------------

def administrador_requerido(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()

        if claims.get("rol") != "ADMINISTRADOR":
            return jsonify({
                "error": "No tienes permisos para realizar esta operación"
            }), 403

        return func(*args, **kwargs)

    return wrapper


# --------------------------------------------------
# FUNCIONES AUXILIARES
# --------------------------------------------------

def serializar_usuario(usuario):
    rol = db.session.get(Rol, usuario.id_rol)

    return {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "ci": usuario.ci,
        "telefono": usuario.telefono,
        "email": usuario.email,
        "rol": rol.nombre_rol if rol else None,
        "id_empresa": usuario.id_empresa,
        "id_estacion": usuario.id_estacion,
        "activo": usuario.activo,
    }


def validar_email(email):
    try:
        resultado = validate_email(
            email,
            check_deliverability=False
        )
        return resultado.normalized
    except EmailNotValidError:
        return None


def validar_asociaciones(rol, id_empresa, id_estacion):
    if rol == "TRANSPORTISTA":
        if not id_empresa:
            return "El transportista debe estar asociado a una empresa"

        if db.session.get(Empresa, id_empresa) is None:
            return "La empresa indicada no existe"

        if id_estacion is not None:
            return "El transportista no debe tener una estación asociada"

    elif rol == "DESPACHADOR":
        if not id_estacion:
            return "El despachador debe estar asociado a una estación"

        if db.session.get(Estacion, id_estacion) is None:
            return "La estación indicada no existe"

        if id_empresa is not None:
            return "El despachador no debe tener una empresa asociada"

    elif rol == "ADMINISTRADOR":
        if id_empresa is not None or id_estacion is not None:
            return "El administrador no debe tener empresa ni estación asociada"

    return None


# --------------------------------------------------
# REGISTRAR USUARIO
# POST /api/usuarios
# --------------------------------------------------

@usuarios_bp.post("")
@administrador_requerido
def crear_usuario():

    data = request.get_json(silent=True) or {}

    nombre = str(data.get("nombre", "")).strip()
    apellido = str(data.get("apellido", "")).strip()
    ci = str(data.get("ci", "")).strip() or None
    telefono = str(data.get("telefono", "")).strip() or None
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")
    nombre_rol = str(data.get("rol", "")).strip().upper()

    if not all([nombre, apellido, email, password, nombre_rol]):
        return jsonify({
            "error": "Nombre, apellido, correo, contraseña y rol son obligatorios"
        }), 400

    if len(nombre) > 100 or len(apellido) > 150:
        return jsonify({
            "error": "El nombre o apellido excede la longitud permitida"
        }), 400

    if len(password) < 12:
        return jsonify({
            "error": "La contraseña debe tener al menos 12 caracteres"
        }), 400

    email_validado = validar_email(email)

    if not email_validado:
        return jsonify({
            "error": "El correo electrónico no tiene un formato válido"
        }), 400

    if nombre_rol not in [
        "ADMINISTRADOR",
        "TRANSPORTISTA",
        "DESPACHADOR"
    ]:
        return jsonify({
            "error": "Rol no válido"
        }), 400

    rol = Rol.query.filter_by(nombre_rol=nombre_rol).first()

    if rol is None:
        return jsonify({
            "error": "El rol indicado no existe en la base de datos"
        }), 400

    if Usuario.query.filter_by(email=email_validado).first():
        return jsonify({
            "error": "El correo electrónico ya está registrado"
        }), 409

    if ci and Usuario.query.filter_by(ci=ci).first():
        return jsonify({
            "error": "La CI ya está registrada"
        }), 409

    if nombre_rol == "TRANSPORTISTA":
        if not ci or not telefono:
            return jsonify({
                "error": "El transportista requiere CI y teléfono"
            }), 400

    id_empresa = data.get("id_empresa")
    id_estacion = data.get("id_estacion")

    try:
        if id_empresa is not None:
            id_empresa = int(id_empresa)

        if id_estacion is not None:
            id_estacion = int(id_estacion)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Los identificadores de empresa y estación deben ser números"
        }), 400

    error_asociacion = validar_asociaciones(
        nombre_rol,
        id_empresa,
        id_estacion
    )

    if error_asociacion:
        return jsonify({"error": error_asociacion}), 400

    if telefono and len(telefono) > 30:
        return jsonify({
            "error": "El teléfono excede los 30 caracteres"
        }), 400

    usuario = Usuario(
        id_rol=rol.id_rol,
        id_empresa=id_empresa,
        id_estacion=id_estacion,
        nombre=nombre,
        apellido=apellido,
        ci=ci,
        telefono=telefono,
        email=email_validado,
        password_hash=bcrypt.generate_password_hash(
            password
        ).decode("utf-8"),
        activo=True,
    )

    try:
        db.session.add(usuario)
        db.session.commit()

        return jsonify({
            "mensaje": "Usuario creado correctamente",
            "usuario": serializar_usuario(usuario)
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "No se pudo crear el usuario. Verifica correo y CI duplicados."
        }), 409


# --------------------------------------------------
# LISTAR USUARIOS
# GET /api/usuarios
# --------------------------------------------------

@usuarios_bp.get("")
@administrador_requerido
def listar_usuarios():

    usuarios = Usuario.query.order_by(
        Usuario.id_usuario
    ).all()

    return jsonify({
        "total": len(usuarios),
        "usuarios": [
            serializar_usuario(usuario)
            for usuario in usuarios
        ]
    }), 200


# --------------------------------------------------
# CONSULTAR USUARIO POR ID
# GET /api/usuarios/<id>
# --------------------------------------------------

@usuarios_bp.get("/<int:id_usuario>")
@administrador_requerido
def obtener_usuario(id_usuario):

    usuario = db.session.get(Usuario, id_usuario)

    if usuario is None:
        return jsonify({
            "error": "Usuario no encontrado"
        }), 404

    return jsonify(serializar_usuario(usuario)), 200


# --------------------------------------------------
# MODIFICAR DATOS DEL USUARIO
# PATCH /api/usuarios/<id>
# --------------------------------------------------

@usuarios_bp.patch("/<int:id_usuario>")
@administrador_requerido
def modificar_usuario(id_usuario):

    usuario = db.session.get(Usuario, id_usuario)

    if usuario is None:
        return jsonify({
            "error": "Usuario no encontrado"
        }), 404

    data = request.get_json(silent=True) or {}

    campos_permitidos = [
        "nombre",
        "apellido",
        "ci",
        "telefono",
        "email",
        "id_empresa",
        "id_estacion",
    ]

    for campo in data:
        if campo not in campos_permitidos:
            return jsonify({
                "error": f"No se permite modificar el campo: {campo}"
            }), 400

    nombre = str(data.get("nombre", usuario.nombre)).strip()
    apellido = str(data.get("apellido", usuario.apellido)).strip()
    ci = str(data.get("ci", usuario.ci or "")).strip() or None
    telefono = str(data.get("telefono", usuario.telefono or "")).strip() or None
    email = str(data.get("email", usuario.email)).strip().lower()

    if not nombre or not apellido or len(nombre) > 100 or len(apellido) > 150:
        return jsonify({
            "error": "Nombre y apellido son obligatorios y deben tener una longitud válida"
        }), 400

    email_validado = validar_email(email)

    if not email_validado:
        return jsonify({
            "error": "Correo electrónico no válido"
        }), 400

    duplicado_email = Usuario.query.filter(
        Usuario.email == email_validado,
        Usuario.id_usuario != id_usuario
    ).first()

    if duplicado_email:
        return jsonify({
            "error": "El correo ya pertenece a otro usuario"
        }), 409

    duplicado_ci = None

    if ci:
        duplicado_ci = Usuario.query.filter(
            Usuario.ci == ci,
            Usuario.id_usuario != id_usuario
        ).first()

    if duplicado_ci:
        return jsonify({
            "error": "La CI ya pertenece a otro usuario"
        }), 409

    try:
        id_empresa = data.get("id_empresa", usuario.id_empresa)
        id_estacion = data.get("id_estacion", usuario.id_estacion)

        if id_empresa is not None:
            id_empresa = int(id_empresa)

        if id_estacion is not None:
            id_estacion = int(id_estacion)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Los identificadores deben ser números"
        }), 400

    rol = db.session.get(Rol, usuario.id_rol)

    error_asociacion = validar_asociaciones(
        rol.nombre_rol,
        id_empresa,
        id_estacion
    )

    if error_asociacion:
        return jsonify({"error": error_asociacion}), 400

    if rol.nombre_rol == "TRANSPORTISTA":
        if not ci or not telefono:
            return jsonify({
                "error": "El transportista requiere CI y teléfono"
            }), 400

    if telefono and len(telefono) > 30:
        return jsonify({
            "error": "El teléfono excede los 30 caracteres"
        }), 400

    usuario.nombre = nombre
    usuario.apellido = apellido
    usuario.ci = ci
    usuario.telefono = telefono
    usuario.email = email_validado
    usuario.id_empresa = id_empresa
    usuario.id_estacion = id_estacion

    try:
        db.session.commit()

        return jsonify({
            "mensaje": "Usuario actualizado correctamente",
            "usuario": serializar_usuario(usuario)
        }), 200

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "No se pudo actualizar el usuario por datos duplicados"
        }), 409


# --------------------------------------------------
# ACTIVAR / DESACTIVAR USUARIO
# PATCH /api/usuarios/<id>/estado
# --------------------------------------------------

@usuarios_bp.patch("/<int:id_usuario>/estado")
@administrador_requerido
def cambiar_estado_usuario(id_usuario):

    usuario = db.session.get(Usuario, id_usuario)

    if usuario is None:
        return jsonify({
            "error": "Usuario no encontrado"
        }), 404

    data = request.get_json(silent=True) or {}
    activo = data.get("activo")

    if not isinstance(activo, bool):
        return jsonify({
            "error": "El campo activo debe ser true o false"
        }), 400

    claims = get_jwt()
    usuario_actual_id = int(claims.get("sub"))

    if usuario.id_usuario == usuario_actual_id and activo is False:
        return jsonify({
            "error": "No puedes desactivar tu propia cuenta"
        }), 400

    usuario.activo = activo
    db.session.commit()

    return jsonify({
        "mensaje": "Estado actualizado correctamente",
        "usuario": serializar_usuario(usuario)
    }), 200