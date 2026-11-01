from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from functools import wraps

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import (
    CupoSemanal,
    Vehiculo,
    Usuario,
    AsignacionVehiculo,
)

cupos_bp = Blueprint("cupos", __name__)

ZONA_BOLIVIA = ZoneInfo("America/La_Paz")


def solo_administrador(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()

        if claims.get("rol") != "ADMINISTRADOR":
            return jsonify({
                "error": "No tienes permisos para realizar esta operación"
            }), 403

        return fn(*args, **kwargs)

    return wrapper


def obtener_semana(fecha):
    """
    Recibe una fecha y devuelve el lunes y domingo
    de la semana correspondiente.
    """
    lunes = fecha - timedelta(days=fecha.weekday())
    domingo = lunes + timedelta(days=6)

    return lunes, domingo


def serializar_cupo(cupo):
    return {
        "id_cupo": cupo.id_cupo,
        "id_vehiculo": cupo.id_vehiculo,
        "id_usuario_asigna": cupo.id_usuario_asigna,
        "litros_asignados": float(cupo.litros_asignados),
        "litros_disponibles": float(cupo.litros_disponibles),
        "fecha_inicio": cupo.fecha_inicio.isoformat(),
        "fecha_fin": cupo.fecha_fin.isoformat(),
        "fecha_asignacion": (
            cupo.fecha_asignacion.isoformat()
            if cupo.fecha_asignacion
            else None
        ),
    }


@cupos_bp.route("", methods=["POST"])
@solo_administrador
def crear_cupo():
    datos = request.get_json(silent=True) or {}

    id_vehiculo = datos.get("id_vehiculo")
    litros_asignados = datos.get("litros_asignados")
    fecha_inicio_texto = datos.get("fecha_inicio")

    if not id_vehiculo or litros_asignados is None:
        return jsonify({
            "error": "id_vehiculo y litros_asignados son obligatorios"
        }), 400

    try:
        litros_asignados = float(litros_asignados)
    except (TypeError, ValueError):
        return jsonify({
            "error": "litros_asignados debe ser un número"
        }), 400

    if litros_asignados <= 0:
        return jsonify({
            "error": "Los litros asignados deben ser mayores a cero"
        }), 400

    # La semana se determina usando la fecha local de Bolivia.
    if fecha_inicio_texto:
        try:
            fecha_solicitada = date.fromisoformat(fecha_inicio_texto)
        except (TypeError, ValueError):
            return jsonify({
                "error": "fecha_inicio debe tener formato YYYY-MM-DD"
            }), 400
    else:
        fecha_solicitada = datetime.now(
            ZONA_BOLIVIA
        ).date()

    fecha_inicio, fecha_fin = obtener_semana(fecha_solicitada)

    # Validar que el vehículo exista y esté activo.
    vehiculo = db.session.get(Vehiculo, id_vehiculo)

    if not vehiculo:
        return jsonify({
            "error": "El vehículo no existe"
        }), 404

    if not vehiculo.activo:
        return jsonify({
            "error": "No se puede asignar un cupo a un vehículo inactivo"
        }), 400

    # Debe existir al menos un transportista activo asignado al vehículo.
    asignacion_activa = (
        db.session.query(AsignacionVehiculo)
        .join(
            Usuario,
            AsignacionVehiculo.id_usuario == Usuario.id_usuario
        )
        .filter(
            AsignacionVehiculo.id_vehiculo == id_vehiculo,
            AsignacionVehiculo.activa.is_(True),
            Usuario.activo.is_(True),
        )
        .first()
    )

    if not asignacion_activa:
        return jsonify({
            "error": (
                "El vehículo debe tener un transportista activo "
                "asignado antes de crear un cupo"
            )
        }), 409

    # Regla: máximo un cupo por vehículo por semana.
    cupo_existente = (
        CupoSemanal.query
        .filter_by(
            id_vehiculo=id_vehiculo,
            fecha_inicio=fecha_inicio,
        )
        .first()
    )

    if cupo_existente:
        return jsonify({
            "error": (
                "Ya existe un cupo para este vehículo "
                "en la semana seleccionada"
            ),
            "id_cupo": cupo_existente.id_cupo,
        }), 409

    claims = get_jwt()
    id_usuario_asigna = claims.get("id_usuario")

    if not id_usuario_asigna:
        return jsonify({
            "error": "El token no contiene el identificador del usuario"
        }), 401

    cupo = CupoSemanal(
        id_vehiculo=id_vehiculo,
        id_usuario_asigna=id_usuario_asigna,
        litros_asignados=litros_asignados,
        litros_disponibles=litros_asignados,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        fecha_asignacion=datetime.now(ZONA_BOLIVIA),
    )

    try:
        db.session.add(cupo)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        # También cubre solicitudes concurrentes que intenten
        # crear el mismo cupo al mismo tiempo.
        return jsonify({
            "error": (
                "Ya existe un cupo para este vehículo "
                "en la semana seleccionada"
            )
        }), 409

    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "No se pudo crear el cupo"
        }), 500

    return jsonify({
        "mensaje": "Cupo semanal creado correctamente",
        "cupo": serializar_cupo(cupo),
    }), 201


@cupos_bp.route("", methods=["GET"])
@solo_administrador
def listar_cupos():
    consulta = CupoSemanal.query

    # id_vehiculo = request.args.get("id_vehiculo")
    # fecha_texto = request.args.get("fecha")

    # if id_vehiculo:
    #     consulta = consulta.filter_by(id_vehiculo=id_vehiculo)

    id_vehiculo = request.args.get("id_vehiculo")
    fecha_texto = request.args.get("fecha")

    if id_vehiculo is not None:
        try:
            id_vehiculo = int(id_vehiculo)
        except (TypeError, ValueError):
            return jsonify({
                "error": "El id_vehiculo debe ser un número entero"
            }), 400

        if id_vehiculo <= 0:
            return jsonify({
                "error": "El id_vehiculo debe ser mayor a cero"
            }), 400

        consulta = consulta.filter_by(id_vehiculo=id_vehiculo)
        

    if fecha_texto:
        try:
            fecha = date.fromisoformat(fecha_texto)
        except ValueError:
            return jsonify({
                "error": "fecha debe tener formato YYYY-MM-DD"
            }), 400

        lunes, _ = obtener_semana(fecha)

        consulta = consulta.filter_by(fecha_inicio=lunes)

    cupos = (
        consulta
        .order_by(CupoSemanal.fecha_inicio.desc())
        .all()
    )

    return jsonify([
        serializar_cupo(cupo)
        for cupo in cupos
    ]), 200


@cupos_bp.route("/<int:id_cupo>", methods=["GET"])
@solo_administrador
def obtener_cupo(id_cupo):
    cupo = db.session.get(CupoSemanal, id_cupo)

    if not cupo:
        return jsonify({
            "error": "El cupo no existe"
        }), 404

    return jsonify({
        "cupo": serializar_cupo(cupo)
    }), 200