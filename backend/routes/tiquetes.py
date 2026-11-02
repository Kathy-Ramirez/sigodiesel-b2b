from datetime import datetime
from zoneinfo import ZoneInfo
from functools import wraps
from uuid import uuid4

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import CupoSemanal, TiquetDigital

tiquetes_bp = Blueprint("tiquetes", __name__)

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


def ahora_bolivia():
    return datetime.now(ZONA_BOLIVIA)


def serializar_tiquet(tiquet):
    return {
        "id_tiquet": tiquet.id_tiquet,
        "id_cupo": tiquet.id_cupo,
        "token_qr": str(tiquet.token_qr),
        "estado": tiquet.estado,
        "fecha_generacion": (
            tiquet.fecha_generacion.isoformat()
            if tiquet.fecha_generacion
            else None
        ),
        "fecha_desactivacion": (
            tiquet.fecha_desactivacion.isoformat()
            if tiquet.fecha_desactivacion
            else None
        ),
    }


def cupo_vigente(cupo):
    """
    El cupo es válido desde su fecha_inicio hasta fecha_fin,
    ambas incluidas, usando la fecha local de Bolivia.
    """
    hoy = ahora_bolivia().date()

    return cupo.fecha_inicio <= hoy <= cupo.fecha_fin


@tiquetes_bp.route("/cupo/<int:id_cupo>", methods=["POST"])
@solo_administrador
def generar_tiquete(id_cupo):
    cupo = db.session.get(CupoSemanal, id_cupo)

    if not cupo:
        return jsonify({
            "error": "El cupo no existe"
        }), 404

    if not cupo_vigente(cupo):
        return jsonify({
            "error": "No se puede generar un QR para un cupo fuera de su semana"
        }), 409

    # Si ya existe un tiquete vigente, no se crea otro.
    tiquete_existente = (
        TiquetDigital.query
        .filter_by(
            id_cupo=id_cupo,
            estado="VIGENTE",
        )
        .first()
    )

    if tiquete_existente:
        return jsonify({
            "error": "Este cupo ya tiene un tiquete QR vigente",
            "tiquete": serializar_tiquet(tiquete_existente),
        }), 409

    claims = get_jwt()
    id_usuario_genera = claims.get("id_usuario")

    if not id_usuario_genera:
        return jsonify({
            "error": "El token no contiene el identificador del usuario"
        }), 401

    tiquete = TiquetDigital(
        id_cupo=id_cupo,
        id_usuario_genera=id_usuario_genera,
        token_qr=str(uuid4()),
        estado="VIGENTE",
        fecha_generacion=ahora_bolivia(),
        fecha_desactivacion=None,
    )

    try:
        db.session.add(tiquete)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "error": "No se pudo crear el tiquete. Verifica si ya existe uno vigente."
        }), 409

    except Exception:
        db.session.rollback()

        return jsonify({
            "error": "Ocurrió un error al generar el tiquete"
        }), 500

    return jsonify({
        "mensaje": "Tiquete QR generado correctamente",
        "tiquete": serializar_tiquet(tiquete),
    }), 201


@tiquetes_bp.route("/cupo/<int:id_cupo>", methods=["GET"])
@solo_administrador
def consultar_tiquete(id_cupo):
    cupo = db.session.get(CupoSemanal, id_cupo)

    if not cupo:
        return jsonify({
            "error": "El cupo no existe"
        }), 404

    tiquete = (
        TiquetDigital.query
        .filter_by(
            id_cupo=id_cupo,
            estado="VIGENTE",
        )
        .first()
    )

    if not tiquete:
        return jsonify({
            "mensaje": "El cupo no tiene un tiquete QR vigente",
            "tiquete": None,
        }), 200

    # Si la semana ya terminó, se marca como EXPIRADO.
    if not cupo_vigente(cupo):
        tiquete.estado = "EXPIRADO"
        tiquete.fecha_desactivacion = ahora_bolivia()
        db.session.commit()

        return jsonify({
            "mensaje": "El tiquete QR ha expirado",
            "tiquete": serializar_tiquet(tiquete),
        }), 200

    return jsonify({
        "tiquete": serializar_tiquet(tiquete)
    }), 200


@tiquetes_bp.route("/cupo/<int:id_cupo>/regenerar", methods=["POST"])
@solo_administrador
def regenerar_tiquete(id_cupo):
    cupo = db.session.get(CupoSemanal, id_cupo)

    if not cupo:
        return jsonify({
            "error": "El cupo no existe"
        }), 404

    if not cupo_vigente(cupo):
        return jsonify({
            "error": "No se puede regenerar un QR para un cupo fuera de su semana"
        }), 409

    claims = get_jwt()
    id_usuario_genera = claims.get("id_usuario")

    if not id_usuario_genera:
        return jsonify({
            "error": "El token no contiene el identificador del usuario"
        }), 401

    try:
        # Invalida el tiquete vigente anterior.
        anterior = (
            TiquetDigital.query
            .filter_by(
                id_cupo=id_cupo,
                estado="VIGENTE",
            )
            .with_for_update()
            .first()
        )

        if anterior:
            anterior.estado = "ANULADO"
            anterior.fecha_desactivacion = ahora_bolivia()

        # Crea un token nuevo.
        nuevo = TiquetDigital(
            id_cupo=id_cupo,
            id_usuario_genera=id_usuario_genera,
            token_qr=str(uuid4()),
            estado="VIGENTE",
            fecha_generacion=ahora_bolivia(),
            fecha_desactivacion=None,
        )

        db.session.add(nuevo)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "error": "No se pudo regenerar el tiquete. Intenta nuevamente."
        }), 409

    except Exception:
        db.session.rollback()

        return jsonify({
            "error": "Ocurrió un error al regenerar el tiquete"
        }), 500

    return jsonify({
        "mensaje": "Tiquete QR regenerado correctamente",
        "tiquete_anterior": (
            serializar_tiquet(anterior)
            if anterior
            else None
        ),
        "tiquete_nuevo": serializar_tiquet(nuevo),
    }), 200
