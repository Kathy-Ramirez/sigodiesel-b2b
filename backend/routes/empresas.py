from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Empresa, Usuario, Vehiculo


empresas_bp = Blueprint("empresas", __name__)


def administrador_requerido(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get("rol") != "ADMINISTRADOR":
            return jsonify({"error": "Acceso exclusivo para administradores"}), 403
        return func(*args, **kwargs)
    return wrapper


def serializar_empresa(empresa):
    return {
        "id_empresa": empresa.id_empresa,
        "nombre_empresa": empresa.nombre_empresa,
        "nit": empresa.nit,
        "telefono": empresa.telefono,
        "activa": empresa.activa,
    }


# POST /api/empresas
@empresas_bp.post("")
@administrador_requerido
def crear_empresa():
    data = request.get_json(silent=True) or {}

    nombre = str(data.get("nombre_empresa", "")).strip()
    nit = str(data.get("nit", "")).strip()
    telefono = str(data.get("telefono", "")).strip() or None

    if not nombre or not nit:
        return jsonify({
            "error": "El nombre de la empresa y el NIT son obligatorios"
        }), 400

    if len(nombre) > 150 or len(nit) > 30:
        return jsonify({"error": "El nombre o NIT excede la longitud permitida"}), 400

    if telefono and len(telefono) > 30:
        return jsonify({"error": "El teléfono no puede superar 30 caracteres"}), 400

    if Empresa.query.filter_by(nit=nit).first():
        return jsonify({"error": "El NIT ya está registrado"}), 409

    empresa = Empresa(
        nombre_empresa=nombre,
        nit=nit,
        telefono=telefono,
        activa=True,
    )

    try:
        db.session.add(empresa)
        db.session.commit()
        return jsonify({
            "mensaje": "Empresa creada correctamente",
            "empresa": serializar_empresa(empresa),
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "No se pudo crear la empresa; verifica el NIT"}), 409


# GET /api/empresas
@empresas_bp.get("")
@administrador_requerido
def listar_empresas():
    empresas = Empresa.query.order_by(Empresa.id_empresa).all()

    return jsonify({
        "total": len(empresas),
        "empresas": [serializar_empresa(e) for e in empresas],
    }), 200


# GET /api/empresas/<id>
@empresas_bp.get("/<int:id_empresa>")
@administrador_requerido
def obtener_empresa(id_empresa):
    empresa = db.session.get(Empresa, id_empresa)

    if empresa is None:
        return jsonify({"error": "Empresa no encontrada"}), 404

    return jsonify(serializar_empresa(empresa)), 200


# PATCH /api/empresas/<id>
@empresas_bp.patch("/<int:id_empresa>")
@administrador_requerido
def modificar_empresa(id_empresa):
    empresa = db.session.get(Empresa, id_empresa)

    if empresa is None:
        return jsonify({"error": "Empresa no encontrada"}), 404

    data = request.get_json(silent=True) or {}
    permitidos = {"nombre_empresa", "nit", "telefono"}

    if not data or not set(data).issubset(permitidos):
        return jsonify({
            "error": "Envía al menos un campo permitido: nombre_empresa, nit o telefono"
        }), 400

    if "nombre_empresa" in data:
        nombre = str(data["nombre_empresa"]).strip()
        if not nombre or len(nombre) > 150:
            return jsonify({"error": "Nombre de empresa no válido"}), 400
        empresa.nombre_empresa = nombre

    if "nit" in data:
        nit = str(data["nit"]).strip()
        if not nit or len(nit) > 30:
            return jsonify({"error": "NIT no válido"}), 400

        duplicado = Empresa.query.filter(
            Empresa.nit == nit,
            Empresa.id_empresa != id_empresa,
        ).first()

        if duplicado:
            return jsonify({"error": "El NIT ya pertenece a otra empresa"}), 409

        empresa.nit = nit

    if "telefono" in data:
        telefono = str(data["telefono"]).strip() or None
        if telefono and len(telefono) > 30:
            return jsonify({"error": "Teléfono demasiado largo"}), 400
        empresa.telefono = telefono

    try:
        db.session.commit()
        return jsonify({
            "mensaje": "Empresa actualizada correctamente",
            "empresa": serializar_empresa(empresa),
        }), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "No se pudo actualizar la empresa"}), 409


# PATCH /api/empresas/<id>/estado
@empresas_bp.patch("/<int:id_empresa>/estado")
@administrador_requerido
def cambiar_estado_empresa(id_empresa):
    empresa = db.session.get(Empresa, id_empresa)

    if empresa is None:
        return jsonify({"error": "Empresa no encontrada"}), 404

    data = request.get_json(silent=True) or {}
    activa = data.get("activa")

    if not isinstance(activa, bool):
        return jsonify({"error": "El campo activa debe ser true o false"}), 400

    if activa is False:
        tiene_usuarios = Usuario.query.filter_by(
            id_empresa=id_empresa,
            activo=True,
        ).first()

        tiene_vehiculos = Vehiculo.query.filter_by(
            id_empresa=id_empresa,
            activo=True,
        ).first()

        if tiene_usuarios or tiene_vehiculos:
            return jsonify({
                "error": "No se puede desactivar: la empresa tiene usuarios transportistas o vehículos activos"
            }), 409

    empresa.activa = activa
    db.session.commit()

    return jsonify({
        "mensaje": "Estado de la empresa actualizado",
        "empresa": serializar_empresa(empresa),
    }), 200