from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from uuid import uuid4

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import (
    Usuario,
    AsignacionVehiculo,
    Vehiculo,
    Empresa,
    CupoSemanal,
    TiquetDigital,
    Estacion, 
    TransaccionDespacho
)

transportistas_bp = Blueprint("transportistas", __name__)

ZONA_BOLIVIA = ZoneInfo("America/La_Paz")


def obtener_transportista_autenticado():
    claims = get_jwt()

    if claims.get("rol") != "TRANSPORTISTA":
        return None, (jsonify({
            "error": "No tienes permisos para realizar esta operación"
        }), 403)

    id_usuario = claims.get("id_usuario")

    if not id_usuario:
        return None, (jsonify({
            "error": "El token no contiene el identificador del usuario"
        }), 401)

    usuario = db.session.get(Usuario, id_usuario)

    if not usuario or not usuario.activo:
        return None, (jsonify({
            "error": "El usuario no existe o está inactivo"
        }), 403)

    return usuario, None


def obtener_cupo_del_transportista(id_cupo, id_usuario):
    return (
        db.session.query(CupoSemanal)
        .join(
            Vehiculo,
            Vehiculo.id_vehiculo == CupoSemanal.id_vehiculo
        )
        .join(
            Empresa,
            Empresa.id_empresa == Vehiculo.id_empresa
        )
        .join(
            AsignacionVehiculo,
            AsignacionVehiculo.id_vehiculo == Vehiculo.id_vehiculo
        )
        .filter(
            CupoSemanal.id_cupo == id_cupo,
            AsignacionVehiculo.id_usuario == id_usuario,
            AsignacionVehiculo.activa.is_(True),
            Vehiculo.activo.is_(True),
            Empresa.activa.is_(True)
        )
        .first()
    )


def semana_actual_bolivia():
    hoy = datetime.now(ZONA_BOLIVIA).date()
    inicio = hoy - timedelta(days=hoy.weekday())
    fin = inicio + timedelta(days=6)

    return inicio, fin


def serializar_tiquete(tiquete):
    return {
        "id_tiquet": tiquete.id_tiquet,
        "id_cupo": tiquete.id_cupo,
        "token_qr": str(tiquete.token_qr),
        "estado": tiquete.estado,
        "fecha_generacion": (
            tiquete.fecha_generacion.isoformat()
            if tiquete.fecha_generacion else None
        ),
        "fecha_desactivacion": (
            tiquete.fecha_desactivacion.isoformat()
            if tiquete.fecha_desactivacion else None
        )
    }


@transportistas_bp.route("/vehiculos", methods=["GET"])
@jwt_required()
def listar_vehiculos_asignados():
    """
    Lista únicamente los vehículos activos asignados
    al transportista autenticado.
    """

    claims = get_jwt()

    # 1. Verificar que el usuario tenga el rol TRANSPORTISTA
    if claims.get("rol") != "TRANSPORTISTA":
        return jsonify({
            "error": "No tienes permisos para consultar esta información"
        }), 403

    # 2. Obtener el ID del usuario desde el token JWT
    id_usuario = claims.get("id_usuario")

    if not id_usuario:
        return jsonify({
            "error": "El token no contiene el identificador del usuario"
        }), 401

    # 3. Verificar que el transportista exista y esté activo
    usuario = db.session.get(Usuario, id_usuario)

    if not usuario or not usuario.activo:
        return jsonify({
            "error": "El usuario no existe o está inactivo"
        }), 403

    # 4. Consultar únicamente sus asignaciones activas,
    # vehículos activos y empresas activas.
    resultados = (
        db.session.query(
            AsignacionVehiculo.id_asignacion,
            Vehiculo.id_vehiculo,
            Vehiculo.placa,
            Vehiculo.modelo,
            Vehiculo.capacidad_tanque,
            Empresa.id_empresa,
            Empresa.nombre_empresa
        )
        .join(
            Vehiculo,
            Vehiculo.id_vehiculo == AsignacionVehiculo.id_vehiculo
        )
        .join(
            Empresa,
            Empresa.id_empresa == Vehiculo.id_empresa
        )
        .filter(
            AsignacionVehiculo.id_usuario == id_usuario,
            AsignacionVehiculo.activa.is_(True),
            Vehiculo.activo.is_(True),
            Empresa.activa.is_(True)
        )
        .order_by(Vehiculo.placa.asc())
        .all()
    )

    # 5. Preparar la respuesta
    vehiculos = []

    for fila in resultados:
        vehiculos.append({
            "id_asignacion": fila.id_asignacion,
            "id_vehiculo": fila.id_vehiculo,
            "placa": fila.placa,
            "modelo": fila.modelo,
            "capacidad_tanque": float(fila.capacidad_tanque),
            "id_empresa": fila.id_empresa,
            "nombre_empresa": fila.nombre_empresa
        })

    return jsonify({
        "mensaje": "Vehículos asignados consultados correctamente",
        "total": len(vehiculos),
        "vehiculos": vehiculos
    }), 200


@transportistas_bp.route("/cupos", methods=["GET"])
@jwt_required()
def listar_cupos_transportista():

    claims = get_jwt()

    # 1. Verificar el rol
    if claims.get("rol") != "TRANSPORTISTA":
        return jsonify({
            "error": "No tienes permisos para consultar esta información"
        }), 403

    id_usuario = claims.get("id_usuario")

    if not id_usuario:
        return jsonify({
            "error": "El token no contiene el identificador del usuario"
        }), 401

    # 2. Verificar que el transportista esté activo
    usuario = db.session.get(Usuario, id_usuario)

    if not usuario or not usuario.activo:
        return jsonify({
            "error": "El usuario no existe o está inactivo"
        }), 403

    # 3. Determinar el periodo solicitado
    periodo = request.args.get("periodo", "todos").lower()

    if periodo not in ["actual", "todos"]:
        return jsonify({
            "error": "El periodo debe ser 'actual' o 'todos'"
        }), 400

    # 4. Obtener la semana actual en horario de Bolivia
    hoy = date.today()  # Se reemplaza inmediatamente por fecha local Bolivia
    hoy = date.today() if False else __import__("datetime").datetime.now(
        ZONA_BOLIVIA
    ).date()

    # hoy = datetime.now(ZONA_BOLIVIA).date()
    # inicio_semana = hoy - __import__("datetime").timedelta(days=hoy.weekday())
    # fin_semana = inicio_semana + __import__("datetime").timedelta(days=6)

    inicio_semana = hoy.fromordinal(
        hoy.toordinal() - hoy.weekday()
    )
    fin_semana = inicio_semana.fromordinal(
        inicio_semana.toordinal() + 6
    )

    # 5. Consultar los cupos de vehículos actualmente asignados
    consulta = (
        db.session.query(CupoSemanal, Vehiculo, Empresa)
        .join(
            Vehiculo,
            Vehiculo.id_vehiculo == CupoSemanal.id_vehiculo
        )
        .join(
            Empresa,
            Empresa.id_empresa == Vehiculo.id_empresa
        )
        .join(
            AsignacionVehiculo,
            AsignacionVehiculo.id_vehiculo == Vehiculo.id_vehiculo
        )
        .filter(
            AsignacionVehiculo.id_usuario == id_usuario,
            AsignacionVehiculo.activa.is_(True),
            Vehiculo.activo.is_(True),
            Empresa.activa.is_(True)
        )
    )

    # 6. Si solicita solamente el periodo actual, filtrar la semana
    if periodo == "actual":
        consulta = consulta.filter(
            CupoSemanal.fecha_inicio == inicio_semana,
            CupoSemanal.fecha_fin == fin_semana
        )

    resultados = (
        consulta
        .order_by(
            CupoSemanal.fecha_inicio.desc(),
            Vehiculo.placa.asc()
        )
        .all()
    )

    # 7. Preparar la respuesta
    cupos = []

    for cupo, vehiculo, empresa in resultados:

        litros_asignados = float(cupo.litros_asignados)
        litros_disponibles = float(cupo.litros_disponibles)

        litros_consumidos = (
            litros_asignados - litros_disponibles
        )

        estado_periodo = (
            "ACTUAL"
            if cupo.fecha_inicio == inicio_semana
            and cupo.fecha_fin == fin_semana
            else "ANTERIOR"
        )

        cupos.append({
            "id_cupo": cupo.id_cupo,
            "id_vehiculo": vehiculo.id_vehiculo,
            "placa": vehiculo.placa,
            "modelo": vehiculo.modelo,
            "nombre_empresa": empresa.nombre_empresa,
            "litros_asignados": litros_asignados,
            "litros_consumidos": litros_consumidos,
            "litros_disponibles": litros_disponibles,
            "fecha_inicio": cupo.fecha_inicio.isoformat(),
            "fecha_fin": cupo.fecha_fin.isoformat(),
            "estado_periodo": estado_periodo
        })

    return jsonify({
        "mensaje": "Cupos consultados correctamente",
        "periodo_consultado": periodo.upper(),
        "total": len(cupos),
        "cupos": cupos
    }), 200


@transportistas_bp.route(
    "/cupos/<int:id_cupo>/tiquete",
    methods=["GET"]
)
@jwt_required()
def consultar_tiquete_transportista(id_cupo):

    usuario, error = obtener_transportista_autenticado()

    if error:
        return error

    cupo = obtener_cupo_del_transportista(
        id_cupo,
        usuario.id_usuario
    )

    if not cupo:
        return jsonify({
            "error": "El cupo no existe o no pertenece a tus vehículos asignados"
        }), 404

    tiquete = (
        TiquetDigital.query
        .filter_by(id_cupo=id_cupo)
        .order_by(TiquetDigital.fecha_generacion.desc())
        .first()
    )

    if not tiquete:
        return jsonify({
            "mensaje": "Este cupo todavía no tiene un tiquete QR",
            "tiquete": None
        }), 200

    return jsonify({
        "mensaje": "Tiquete consultado correctamente",
        "tiquete": serializar_tiquete(tiquete)
    }), 200


@transportistas_bp.route(
    "/cupos/<int:id_cupo>/tiquete",
    methods=["POST"]
)
@jwt_required()
def generar_tiquete_transportista(id_cupo):

    usuario, error = obtener_transportista_autenticado()

    if error:
        return error

    try:
        inicio_semana, fin_semana = semana_actual_bolivia()

        cupo = (
            db.session.query(CupoSemanal)
            .filter_by(id_cupo=id_cupo)
            .with_for_update()
            .first()
        )

        if not cupo:
            return jsonify({
                "error": "El cupo no existe"
            }), 404

        # Verificar que el cupo pertenezca a un vehículo asignado
        cupo_asignado = obtener_cupo_del_transportista(
            id_cupo,
            usuario.id_usuario
        )

        if not cupo_asignado:
            return jsonify({
                "error": "El cupo no pertenece a tus vehículos asignados"
            }), 403

        # El QR solo puede generarse para la semana vigente
        if (
            cupo.fecha_inicio != inicio_semana
            or cupo.fecha_fin != fin_semana
        ):
            return jsonify({
                "error": "No se puede generar un QR para un cupo fuera de su semana de vigencia"
            }), 409

        if cupo.litros_disponibles <= 0:
            return jsonify({
                "error": "El cupo no tiene litros disponibles"
            }), 409

        tiquete_vigente = TiquetDigital.query.filter_by(
            id_cupo=id_cupo,
            estado="VIGENTE"
        ).first()

        if tiquete_vigente:
            return jsonify({
                "error": "Este cupo ya tiene un tiquete vigente. Si deseas otro QR, utiliza la opción de regenerar.",
                "tiquete": serializar_tiquete(tiquete_vigente)
            }), 409

        nuevo_tiquete = TiquetDigital(
            id_cupo=id_cupo,
            id_usuario_genera=usuario.id_usuario,
            token_qr=str(uuid4()),
            estado="VIGENTE",
            fecha_generacion=datetime.now(ZONA_BOLIVIA).replace(
                tzinfo=None
            )
        )

        db.session.add(nuevo_tiquete)
        db.session.commit()

        return jsonify({
            "mensaje": "Tiquete QR generado correctamente",
            "tiquete": serializar_tiquete(nuevo_tiquete)
        }), 201

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "error": "Ya existe un tiquete vigente para este cupo"
        }), 409

    except Exception:
        db.session.rollback()
        raise

@transportistas_bp.route(
    "/cupos/<int:id_cupo>/tiquete/regenerar",
    methods=["POST"]
)
@jwt_required()
def regenerar_tiquete_transportista(id_cupo):

    usuario, error = obtener_transportista_autenticado()

    if error:
        return error

    try:
        inicio_semana, fin_semana = semana_actual_bolivia()

        cupo = (
            db.session.query(CupoSemanal)
            .filter_by(id_cupo=id_cupo)
            .with_for_update()
            .first()
        )

        if not cupo:
            return jsonify({
                "error": "El cupo no existe"
            }), 404

        cupo_asignado = obtener_cupo_del_transportista(
            id_cupo,
            usuario.id_usuario
        )

        if not cupo_asignado:
            return jsonify({
                "error": "El cupo no pertenece a tus vehículos asignados"
            }), 403

        if (
            cupo.fecha_inicio != inicio_semana
            or cupo.fecha_fin != fin_semana
        ):
            return jsonify({
                "error": "No se puede regenerar un QR para un cupo fuera de su semana de vigencia"
            }), 409

        if cupo.litros_disponibles <= 0:
            return jsonify({
                "error": "El cupo no tiene litros disponibles"
            }), 409

        ahora = datetime.now(ZONA_BOLIVIA).replace(tzinfo=None)

        # Invalidar el QR vigente anterior
        tiquete_anterior = TiquetDigital.query.filter_by(
            id_cupo=id_cupo,
            estado="VIGENTE"
        ).first()

        if tiquete_anterior:
            tiquete_anterior.estado = "ANULADO"
            tiquete_anterior.fecha_desactivacion = ahora

        # Crear el nuevo QR
        nuevo_tiquete = TiquetDigital(
            id_cupo=id_cupo,
            id_usuario_genera=usuario.id_usuario,
            token_qr=str(uuid4()),
            estado="VIGENTE",
            fecha_generacion=ahora
        )

        db.session.add(nuevo_tiquete)
        db.session.commit()

        return jsonify({
            "mensaje": "Tiquete QR regenerado correctamente. El anterior fue invalidado.",
            "tiquete_anterior": (
                serializar_tiquete(tiquete_anterior)
                if tiquete_anterior else None
            ),
            "nuevo_tiquete": serializar_tiquete(nuevo_tiquete)
        }), 201

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "error": "No se pudo regenerar el tiquete. Verifica si existe otro tiquete vigente."
        }), 409

    except Exception:
        db.session.rollback()
        raise

@transportistas_bp.route("/historial", methods=["GET"])
@jwt_required()
def historial_despachos_transportista():

    # 1. Verificar el transportista autenticado
    usuario, error = obtener_transportista_autenticado()

    if error:
        return error

    # 2. Obtener filtros opcionales
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    placa = request.args.get("placa")
    estado = request.args.get("estado")

    # 3. Validar fechas
    try:
        if fecha_desde:
            fecha_desde = date.fromisoformat(fecha_desde)

        if fecha_hasta:
            fecha_hasta = date.fromisoformat(fecha_hasta)

    except ValueError:
        return jsonify({
            "error": "Las fechas deben tener el formato YYYY-MM-DD"
        }), 400

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        return jsonify({
            "error": "La fecha desde no puede ser posterior a la fecha hasta"
        }), 400

    # 4. Validar estado
    if estado:
        estado = estado.upper()

        if estado not in ["REGISTRADA", "ANULADA"]:
            return jsonify({
                "error": "El estado debe ser REGISTRADA o ANULADA"
            }), 400

    # 5. Consultar únicamente los despachos de vehículos
    # asignados al transportista autenticado
    consulta = (
        db.session.query(
            TransaccionDespacho,
            TiquetDigital,
            CupoSemanal,
            Vehiculo,
            Empresa,
            Estacion
        )
        .join(
            TiquetDigital,
            TiquetDigital.id_tiquet ==
            TransaccionDespacho.id_tiquet
        )
        .join(
            CupoSemanal,
            CupoSemanal.id_cupo == TiquetDigital.id_cupo
        )
        .join(
            Vehiculo,
            Vehiculo.id_vehiculo == CupoSemanal.id_vehiculo
        )
        .join(
            Empresa,
            Empresa.id_empresa == Vehiculo.id_empresa
        )
        .join(
            Estacion,
            Estacion.id_estacion ==
            TransaccionDespacho.id_estacion
        )
        .join(
            AsignacionVehiculo,
            AsignacionVehiculo.id_vehiculo ==
            Vehiculo.id_vehiculo
        )
        .filter(
            AsignacionVehiculo.id_usuario == usuario.id_usuario,
            AsignacionVehiculo.activa.is_(True)
        )
    )

    # 6. Aplicar filtros
    if fecha_desde:
        consulta = consulta.filter(
            TransaccionDespacho.fecha_hora >=
            datetime.combine(fecha_desde, datetime.min.time())
        )

    if fecha_hasta:
        consulta = consulta.filter(
            TransaccionDespacho.fecha_hora <
            datetime.combine(
                fecha_hasta + timedelta(days=1),
                datetime.min.time()
            )
        )

    if placa:
        consulta = consulta.filter(
            Vehiculo.placa.ilike(f"%{placa.strip()}%")
        )

    if estado:
        consulta = consulta.filter(
            TransaccionDespacho.estado == estado
        )

    # 7. Ordenar por fecha más reciente
    resultados = (
        consulta
        .order_by(TransaccionDespacho.fecha_hora.desc())
        .all()
    )

    # 8. Preparar respuesta
    despachos = []

    for transaccion, tiquete, cupo, vehiculo, empresa, estacion in resultados:

        despachos.append({
            "id_transaccion": transaccion.id_transaccion,
            "id_cupo": cupo.id_cupo,
            "id_tiquet": tiquete.id_tiquet,
            "placa": vehiculo.placa,
            "modelo": vehiculo.modelo,
            "nombre_empresa": empresa.nombre_empresa,
            "estacion": estacion.nombre_estacion,
            "codigo_estacion": estacion.codigo,
            "nro_isla": transaccion.nro_isla,
            "litros_cargados": float(transaccion.litros_cargados),
            "fecha_hora": (
                transaccion.fecha_hora.isoformat()
                if transaccion.fecha_hora else None
            ),
            "estado": transaccion.estado,
            "fecha_anulacion": (
                transaccion.fecha_anulacion.isoformat()
                if transaccion.fecha_anulacion else None
            ),
            "motivo_anulacion": transaccion.motivo_anulacion
        })

    return jsonify({
        "mensaje": "Historial de despachos consultado correctamente",
        "total": len(despachos),
        "despachos": despachos
    }), 200