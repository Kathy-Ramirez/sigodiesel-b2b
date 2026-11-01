from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import (
    Usuario,
    Rol,
    Vehiculo,
    AsignacionVehiculo,
)


asignaciones_bp = Blueprint("asignaciones", __name__)


def administrador_requerido(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get("rol") != "ADMINISTRADOR":
            return jsonify({
                "error": "Acceso exclusivo para administradores"
            }), 403
        return func(*args, **kwargs)

    return wrapper


def serializar_asignacion(asignacion):
    usuario = db.session.get(Usuario, asignacion.id_usuario)
    vehiculo = db.session.get(Vehiculo, asignacion.id_vehiculo)

    return {
        "id_asignacion": asignacion.id_asignacion,
        "id_usuario": asignacion.id_usuario,
        "transportista": (
            f"{usuario.nombre} {usuario.apellido}"
            if usuario else None
        ),
        "id_vehiculo": asignacion.id_vehiculo,
        "placa": vehiculo.placa if vehiculo else None,
        "activa": asignacion.activa,
    }


# --------------------------------------------------
# ASIGNAR VEHÍCULO
# POST /api/asignaciones
# --------------------------------------------------

@asignaciones_bp.post("")
@administrador_requerido
def asignar_vehiculo():
    data = request.get_json(silent=True) or {}

    id_usuario = data.get("id_usuario")
    id_vehiculo = data.get("id_vehiculo")

    if id_usuario is None or id_vehiculo is None:
        return jsonify({
            "error": "id_usuario e id_vehiculo son obligatorios"
        }), 400

    try:
        id_usuario = int(id_usuario)
        id_vehiculo = int(id_vehiculo)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Los identificadores deben ser números"
        }), 400

    transportista = db.session.get(Usuario, id_usuario)
    vehiculo = db.session.get(Vehiculo, id_vehiculo)

    if transportista is None or not transportista.activo:
        return jsonify({
            "error": "El transportista no existe o está inactivo"
        }), 404

    if vehiculo is None or not vehiculo.activo:
        return jsonify({
            "error": "El vehículo no existe o está inactivo"
        }), 404

    rol = db.session.get(Rol, transportista.id_rol)

    if rol is None or rol.nombre_rol != "TRANSPORTISTA":
        return jsonify({
            "error": "El usuario indicado no tiene rol TRANSPORTISTA"
        }), 400

    if transportista.id_empresa != vehiculo.id_empresa:
        return jsonify({
            "error": "El vehículo y el transportista deben pertenecer a la misma empresa"
        }), 409

    asignacion = AsignacionVehiculo.query.filter_by(
        id_usuario=id_usuario,
        id_vehiculo=id_vehiculo,
    ).first()

    if asignacion:
        if asignacion.activa:
            return jsonify({
                "error": "El vehículo ya está asignado a este transportista"
            }), 409

        # Reactivar la asignación existente para respetar
        # la restricción única usuario + vehículo.
        asignacion.activa = True

    else:
        asignacion = AsignacionVehiculo(
            id_usuario=id_usuario,
            id_vehiculo=id_vehiculo,
            activa=True,
        )
        db.session.add(asignacion)

    try:
        db.session.commit()

        return jsonify({
            "mensaje": "Vehículo asignado correctamente",
            "asignacion": serializar_asignacion(asignacion),
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "No se pudo registrar la asignación"
        }), 409


# --------------------------------------------------
# LISTAR ASIGNACIONES
# GET /api/asignaciones
# --------------------------------------------------

@asignaciones_bp.get("")
@administrador_requerido
def listar_asignaciones():
    asignaciones = AsignacionVehiculo.query.order_by(
        AsignacionVehiculo.id_asignacion
    ).all()

    return jsonify({
        "total": len(asignaciones),
        "asignaciones": [
            serializar_asignacion(a)
            for a in asignaciones
        ],
    }), 200


# --------------------------------------------------
# ASIGNACIONES DE UN TRANSPORTISTA
# GET /api/asignaciones/transportista/<id>
# --------------------------------------------------

@asignaciones_bp.get("/transportista/<int:id_usuario>")
@administrador_requerido
def asignaciones_transportista(id_usuario):
    transportista = db.session.get(Usuario, id_usuario)

    if transportista is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    rol = db.session.get(Rol, transportista.id_rol)

    if rol is None or rol.nombre_rol != "TRANSPORTISTA":
        return jsonify({
            "error": "El usuario no es transportista"
        }), 400

    asignaciones = AsignacionVehiculo.query.filter_by(
        id_usuario=id_usuario,
        activa=True,
    ).all()

    return jsonify({
        "id_usuario": id_usuario,
        "total": len(asignaciones),
        "asignaciones": [
            serializar_asignacion(a)
            for a in asignaciones
        ],
    }), 200


# --------------------------------------------------
# DESACTIVAR ASIGNACIÓN
# PATCH /api/asignaciones/<id>/estado
# --------------------------------------------------

@asignaciones_bp.patch("/<int:id_asignacion>/estado")
@administrador_requerido
def cambiar_estado_asignacion(id_asignacion):
    asignacion = db.session.get(
        AsignacionVehiculo,
        id_asignacion,
    )

    if asignacion is None:
        return jsonify({"error": "Asignación no encontrada"}), 404

    data = request.get_json(silent=True) or {}
    activa = data.get("activa")

    if not isinstance(activa, bool):
        return jsonify({
            "error": "El campo activa debe ser true o false"
        }), 400

    asignacion.activa = activa
    db.session.commit()

    return jsonify({
        "mensaje": "Estado de la asignación actualizado",
        "asignacion": serializar_asignacion(asignacion),
    }), 200