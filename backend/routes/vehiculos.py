from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import (
    Empresa,
    Usuario,
    Rol,
    Vehiculo,
    AsignacionVehiculo,
    CupoSemanal,
)


vehiculos_bp = Blueprint("vehiculos", __name__)


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


def serializar_vehiculo(vehiculo):
    return {
        "id_vehiculo": vehiculo.id_vehiculo,
        "id_empresa": vehiculo.id_empresa,
        "placa": vehiculo.placa,
        "modelo": vehiculo.modelo,
        "capacidad_tanque": float(vehiculo.capacidad_tanque),
        "activo": vehiculo.activo,
    }


def validar_empresa(id_empresa):
    empresa = db.session.get(Empresa, id_empresa)

    if empresa is None:
        return None, "La empresa indicada no existe"

    if not empresa.activa:
        return None, "La empresa está inactiva"

    return empresa, None


# --------------------------------------------------
# CREAR VEHÍCULO
# POST /api/vehiculos
# --------------------------------------------------

@vehiculos_bp.post("")
@administrador_requerido
def crear_vehiculo():
    data = request.get_json(silent=True) or {}

    placa = str(data.get("placa", "")).strip().upper()
    modelo = str(data.get("modelo", "")).strip() or None
    id_empresa = data.get("id_empresa")
    capacidad = data.get("capacidad_tanque")

    if not placa or id_empresa is None or capacidad is None:
        return jsonify({
            "error": "Placa, empresa y capacidad del tanque son obligatorios"
        }), 400

    if len(placa) > 20:
        return jsonify({"error": "La placa no puede superar 20 caracteres"}), 400

    try:
        id_empresa = int(id_empresa)
        capacidad = float(capacidad)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Empresa y capacidad deben ser valores numéricos válidos"
        }), 400

    if capacidad <= 0:
        return jsonify({
            "error": "La capacidad del tanque debe ser mayor a cero"
        }), 400

    empresa, error = validar_empresa(id_empresa)

    if error:
        return jsonify({"error": error}), 400

    if Vehiculo.query.filter_by(placa=placa).first():
        return jsonify({"error": "La placa ya está registrada"}), 409

    vehiculo = Vehiculo(
        id_empresa=empresa.id_empresa,
        placa=placa,
        modelo=modelo,
        capacidad_tanque=capacidad,
        activo=True,
    )

    try:
        db.session.add(vehiculo)
        db.session.commit()

        return jsonify({
            "mensaje": "Vehículo creado correctamente",
            "vehiculo": serializar_vehiculo(vehiculo),
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "No se pudo crear el vehículo; verifica la placa"
        }), 409


# --------------------------------------------------
# LISTAR VEHÍCULOS
# GET /api/vehiculos
# --------------------------------------------------

@vehiculos_bp.get("")
@administrador_requerido
def listar_vehiculos():
    vehiculos = Vehiculo.query.order_by(
        Vehiculo.id_vehiculo
    ).all()

    return jsonify({
        "total": len(vehiculos),
        "vehiculos": [
            serializar_vehiculo(v)
            for v in vehiculos
        ],
    }), 200


# --------------------------------------------------
# CONSULTAR VEHÍCULO
# GET /api/vehiculos/<id>
# --------------------------------------------------

@vehiculos_bp.get("/<int:id_vehiculo>")
@administrador_requerido
def obtener_vehiculo(id_vehiculo):
    vehiculo = db.session.get(Vehiculo, id_vehiculo)

    if vehiculo is None:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    return jsonify(serializar_vehiculo(vehiculo)), 200


# --------------------------------------------------
# MODIFICAR VEHÍCULO
# PATCH /api/vehiculos/<id>
# --------------------------------------------------

@vehiculos_bp.patch("/<int:id_vehiculo>")
@administrador_requerido
def modificar_vehiculo(id_vehiculo):
    vehiculo = db.session.get(Vehiculo, id_vehiculo)

    if vehiculo is None:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    data = request.get_json(silent=True) or {}
    permitidos = {
        "placa",
        "modelo",
        "capacidad_tanque",
        "id_empresa",
    }

    if not data or not set(data).issubset(permitidos):
        return jsonify({
            "error": "Envía al menos un campo permitido"
        }), 400

    if "placa" in data:
        placa = str(data["placa"]).strip().upper()

        if not placa or len(placa) > 20:
            return jsonify({"error": "Placa no válida"}), 400

        duplicado = Vehiculo.query.filter(
            Vehiculo.placa == placa,
            Vehiculo.id_vehiculo != id_vehiculo,
        ).first()

        if duplicado:
            return jsonify({"error": "La placa ya está registrada"}), 409

        vehiculo.placa = placa

    if "modelo" in data:
        vehiculo.modelo = str(data["modelo"]).strip() or None

    if "capacidad_tanque" in data:
        try:
            capacidad = float(data["capacidad_tanque"])
        except (ValueError, TypeError):
            return jsonify({"error": "Capacidad no válida"}), 400

        if capacidad <= 0:
            return jsonify({
                "error": "La capacidad debe ser mayor a cero"
            }), 400

        vehiculo.capacidad_tanque = capacidad

    if "id_empresa" in data:
        try:
            id_empresa = int(data["id_empresa"])
        except (ValueError, TypeError):
            return jsonify({"error": "ID de empresa no válido"}), 400

        empresa, error = validar_empresa(id_empresa)

        if error:
            return jsonify({"error": error}), 400

        vehiculo.id_empresa = empresa.id_empresa

    try:
        db.session.commit()

        return jsonify({
            "mensaje": "Vehículo actualizado correctamente",
            "vehiculo": serializar_vehiculo(vehiculo),
        }), 200

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "No se pudo actualizar el vehículo"
        }), 409


# --------------------------------------------------
# ACTIVAR / DESACTIVAR VEHÍCULO
# PATCH /api/vehiculos/<id>/estado
# --------------------------------------------------

@vehiculos_bp.patch("/<int:id_vehiculo>/estado")
@administrador_requerido
def cambiar_estado_vehiculo(id_vehiculo):
    vehiculo = db.session.get(Vehiculo, id_vehiculo)

    if vehiculo is None:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    data = request.get_json(silent=True) or {}
    activo = data.get("activo")

    if not isinstance(activo, bool):
        return jsonify({
            "error": "El campo activo debe ser true o false"
        }), 400

    if activo is False:
        tiene_cupo = CupoSemanal.query.filter_by(
            id_vehiculo=id_vehiculo
        ).first()

        if tiene_cupo:
            return jsonify({
                "error": "No se puede desactivar el vehículo porque tiene cupos semanales registrados"
            }), 409

    vehiculo.activo = activo
    db.session.commit()

    return jsonify({
        "mensaje": "Estado del vehículo actualizado",
        "vehiculo": serializar_vehiculo(vehiculo),
    }), 200