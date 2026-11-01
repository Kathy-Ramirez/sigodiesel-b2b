from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Estacion, Usuario, TransaccionDespacho


estaciones_bp = Blueprint("estaciones", __name__)


def administrador_requerido(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get("rol") != "ADMINISTRADOR":
            return jsonify({"error": "Acceso exclusivo para administradores"}), 403
        return func(*args, **kwargs)
    return wrapper


def serializar_estacion(estacion):
    return {
        "id_estacion": estacion.id_estacion,
        "codigo": estacion.codigo,
        "nombre_estacion": estacion.nombre_estacion,
        "direccion": estacion.direccion,
        "ciudad": estacion.ciudad,
        "activa": estacion.activa,
    }


# POST /api/estaciones
@estaciones_bp.post("")
@administrador_requerido
def crear_estacion():
    data = request.get_json(silent=True) or {}

    codigo = str(data.get("codigo", "")).strip().upper()
    nombre = str(data.get("nombre_estacion", "")).strip()
    direccion = str(data.get("direccion", "")).strip() or None
    ciudad = str(data.get("ciudad", "")).strip() or None

    if not codigo or not nombre:
        return jsonify({
            "error": "El código y el nombre de la estación son obligatorios"
        }), 400

    if len(codigo) > 30 or len(nombre) > 150:
        return jsonify({"error": "Código o nombre demasiado largo"}), 400

    if Estacion.query.filter_by(codigo=codigo).first():
        return jsonify({"error": "El código de estación ya existe"}), 409

    estacion = Estacion(
        codigo=codigo,
        nombre_estacion=nombre,
        direccion=direccion,
        ciudad=ciudad,
        activa=True,
    )

    try:
        db.session.add(estacion)
        db.session.commit()
        return jsonify({
            "mensaje": "Estación creada correctamente",
            "estacion": serializar_estacion(estacion),
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "No se pudo crear la estación"}), 409


# GET /api/estaciones
@estaciones_bp.get("")
@administrador_requerido
def listar_estaciones():
    estaciones = Estacion.query.order_by(Estacion.id_estacion).all()

    return jsonify({
        "total": len(estaciones),
        "estaciones": [serializar_estacion(e) for e in estaciones],
    }), 200


# GET /api/estaciones/<id>
@estaciones_bp.get("/<int:id_estacion>")
@administrador_requerido
def obtener_estacion(id_estacion):
    estacion = db.session.get(Estacion, id_estacion)

    if estacion is None:
        return jsonify({"error": "Estación no encontrada"}), 404

    return jsonify(serializar_estacion(estacion)), 200


# PATCH /api/estaciones/<id>
@estaciones_bp.patch("/<int:id_estacion>")
@administrador_requerido
def modificar_estacion(id_estacion):
    estacion = db.session.get(Estacion, id_estacion)

    if estacion is None:
        return jsonify({"error": "Estación no encontrada"}), 404

    data = request.get_json(silent=True) or {}
    permitidos = {"codigo", "nombre_estacion", "direccion", "ciudad"}

    if not data or not set(data).issubset(permitidos):
        return jsonify({
            "error": "Envía al menos un campo permitido: codigo, nombre_estacion, direccion o ciudad"
        }), 400

    if "codigo" in data:
        codigo = str(data["codigo"]).strip().upper()
        if not codigo or len(codigo) > 30:
            return jsonify({"error": "Código no válido"}), 400

        duplicado = Estacion.query.filter(
            Estacion.codigo == codigo,
            Estacion.id_estacion != id_estacion,
        ).first()

        if duplicado:
            return jsonify({"error": "El código ya pertenece a otra estación"}), 409

        estacion.codigo = codigo

    if "nombre_estacion" in data:
        nombre = str(data["nombre_estacion"]).strip()
        if not nombre or len(nombre) > 150:
            return jsonify({"error": "Nombre de estación no válido"}), 400
        estacion.nombre_estacion = nombre

    if "direccion" in data:
        estacion.direccion = str(data["direccion"]).strip() or None

    if "ciudad" in data:
        estacion.ciudad = str(data["ciudad"]).strip() or None

    try:
        db.session.commit()
        return jsonify({
            "mensaje": "Estación actualizada correctamente",
            "estacion": serializar_estacion(estacion),
        }), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "No se pudo actualizar la estación"}), 409


# PATCH /api/estaciones/<id>/estado
@estaciones_bp.patch("/<int:id_estacion>/estado")
@administrador_requerido
def cambiar_estado_estacion(id_estacion):
    estacion = db.session.get(Estacion, id_estacion)

    if estacion is None:
        return jsonify({"error": "Estación no encontrada"}), 404

    data = request.get_json(silent=True) or {}
    activa = data.get("activa")

    if not isinstance(activa, bool):
        return jsonify({"error": "El campo activa debe ser true o false"}), 400

    if activa is False:
        tiene_despachadores = Usuario.query.filter_by(
            id_estacion=id_estacion,
            activo=True,
        ).first()

        if tiene_despachadores:
            return jsonify({
                "error": "No se puede desactivar: la estación tiene despachadores activos"
            }), 409

    estacion.activa = activa
    db.session.commit()

    return jsonify({
        "mensaje": "Estado de la estación actualizado",
        "estacion": serializar_estacion(estacion),
    }), 200