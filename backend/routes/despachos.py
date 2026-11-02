import csv
from io import StringIO
from flask import Response

import traceback
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID
from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import (
    Usuario,
    Estacion,
    TiquetDigital,
    CupoSemanal,
    Vehiculo,
    Empresa,
    TransaccionDespacho,
    AsignacionVehiculo,
)
from zoneinfo import ZoneInfo
from sqlalchemy.exc import SQLAlchemyError


despachos_bp = Blueprint("despachos", __name__)
ZONA_BOLIVIA = ZoneInfo("America/La_Paz")

# import de ytascacion
from sqlalchemy.exc import IntegrityError
from models import TransaccionDespacho

@despachos_bp.route("/validar-qr/<string:token_qr>", methods=["GET"])
@jwt_required()
def validar_qr(token_qr):

    claims = get_jwt()

    # 1. Verificar que sea un despachador
    if claims.get("rol") != "DESPACHADOR":
        return jsonify({
            "error": "No tienes permisos para validar tiquetes"
        }), 403

    id_usuario = claims.get("id_usuario")
    id_estacion = claims.get("id_estacion")

    if not id_usuario or not id_estacion:
        return jsonify({
            "error": "El token no contiene los datos de estación necesarios"
        }), 401

    # 2. Verificar despachador y estación
    despachador = db.session.get(Usuario, id_usuario)

    if not despachador or not despachador.activo:
        return jsonify({
            "error": "El usuario despachador no está activo"
        }), 403

    estacion = db.session.get(Estacion, id_estacion)

    if (
        not estacion
        or not estacion.activa
        or despachador.id_estacion != id_estacion
    ):
        return jsonify({
            "error": "La estación asignada no está activa o no corresponde al despachador"
        }), 403

    # 3. Validar formato UUID del QR
    try:
        token = UUID(token_qr)
    except (ValueError, TypeError, AttributeError):
        return jsonify({
            "error": "El código QR no tiene un formato válido"
        }), 400

    # 4. Buscar tiquete
    tiquete = TiquetDigital.query.filter_by(
        token_qr=token
    ).first()

    if not tiquete:
        return jsonify({
            "error": "El tiquete QR no existe"
        }), 404

    if tiquete.estado != "VIGENTE":
        return jsonify({
            "error": "El tiquete no está vigente",
            "estado": tiquete.estado
        }), 409

    # 5. Buscar cupo semanal
    cupo = db.session.get(CupoSemanal, tiquete.id_cupo)

    if not cupo:
        return jsonify({
            "error": "No se encontró el cupo del tiquete"
        }), 404

    # 6. Validar vigencia semanal
    hoy = datetime.now(ZONA_BOLIVIA).date()

    if hoy < cupo.fecha_inicio or hoy > cupo.fecha_fin:
        tiquete.estado = "EXPIRADO"
        db.session.commit()

        return jsonify({
            "error": "El tiquete está fuera de su semana de vigencia",
            "estado": "EXPIRADO"
        }), 409

    # 7. Validar saldo disponible
    if cupo.litros_disponibles <= Decimal("0"):
        tiquete.estado = "AGOTADO"
        db.session.commit()

        return jsonify({
            "error": "El cupo ya no tiene litros disponibles",
            "estado": "AGOTADO"
        }), 409

    # 8. Buscar vehículo
    vehiculo = db.session.get(
        Vehiculo,
        cupo.id_vehiculo
    )

    if not vehiculo or not vehiculo.activo:
        return jsonify({
            "error": "El vehículo no existe o está inactivo"
        }), 409

    # 9. Buscar empresa
    empresa = db.session.get(
        Empresa,
        vehiculo.id_empresa
    )

    if not empresa or not empresa.activa:
        return jsonify({
            "error": "La empresa del vehículo está inactiva"
        }), 409

    # 10. Respuesta de validación
    return jsonify({
        "mensaje": "Código QR válido. Puede continuar con el despacho",
        "tiquete": {
            "id_tiquet": tiquete.id_tiquet,
            "estado": tiquete.estado
        },
        "vehiculo": {
            "id_vehiculo": vehiculo.id_vehiculo,
            "placa": vehiculo.placa,
            "modelo": vehiculo.modelo,
            "capacidad_tanque": float(vehiculo.capacidad_tanque)
        },
        "empresa": {
            "id_empresa": empresa.id_empresa,
            "nombre_empresa": empresa.nombre_empresa
        },
        "cupo": {
            "id_cupo": cupo.id_cupo,
            "litros_asignados": float(cupo.litros_asignados),
            "litros_disponibles": float(cupo.litros_disponibles),
            "fecha_inicio": cupo.fecha_inicio.isoformat(),
            "fecha_fin": cupo.fecha_fin.isoformat()
        },
        "estacion": {
            "id_estacion": estacion.id_estacion,
            "nombre_estacion": estacion.nombre_estacion
        }
    }), 200



@despachos_bp.route("/registrar", methods=["POST"])
@jwt_required()
def registrar_despacho():

    claims = get_jwt()

    # 1. Verificar rol del usuario
    if claims.get("rol") != "DESPACHADOR":
        return jsonify({
            "error": "No tienes permisos para registrar despachos"
        }), 403

    id_despachador = claims.get("id_usuario")
    id_estacion = claims.get("id_estacion")

    if not id_despachador or not id_estacion:
        return jsonify({
            "error": "El token no contiene los datos del despachador y estación"
        }), 401

    # 2. Recibir datos enviados por la aplicación móvil
    datos = request.get_json(silent=True) or {}

    token_qr = datos.get("token_qr")
    litros_recibidos = datos.get("litros_cargados")
    nro_isla = datos.get("nro_isla")
    id_operacion = datos.get("id_operacion")

    if not all([token_qr, litros_recibidos, nro_isla, id_operacion]):
        return jsonify({
            "error": "Debes enviar token_qr, litros_cargados, nro_isla e id_operacion"
        }), 400

    # 3. Validar identificadores UUID
    try:
        token = UUID(str(token_qr))
        operacion = UUID(str(id_operacion))
    except (ValueError, TypeError, AttributeError):
        return jsonify({
            "error": "El token QR o el identificador de operación no es válido"
        }), 400

    # 4. Validar cantidad de litros
    try:
        litros = Decimal(str(litros_recibidos))
    except (InvalidOperation, ValueError, TypeError):
        return jsonify({
            "error": "La cantidad de litros debe ser numérica"
        }), 400

    if not litros.is_finite() or litros <= Decimal("0"):
        return jsonify({
            "error": "Los litros cargados deben ser mayores que cero"
        }), 400

    # Evitar cantidades con más de dos decimales
    if litros != litros.quantize(Decimal("0.01")):
        return jsonify({
            "error": "La cantidad de litros admite como máximo dos decimales"
        }), 400

    # 5. Validar número de isla
    nro_isla = str(nro_isla).strip()

    if not nro_isla or len(nro_isla) > 20:
        return jsonify({
            "error": "El número de isla es obligatorio y debe tener como máximo 20 caracteres"
        }), 400

    # 6. Comprobar despachador y estación
    despachador = db.session.get(Usuario, id_despachador)
    estacion = db.session.get(Estacion, id_estacion)

    if not despachador or not despachador.activo:
        return jsonify({
            "error": "El despachador no existe o está inactivo"
        }), 403

    if (
        not estacion
        or not estacion.activa
        or despachador.id_estacion != id_estacion
    ):
        return jsonify({
            "error": "La estación no está activa o no corresponde al despachador"
        }), 403

    # 7. Comprobar si la operación ya fue registrada
    existente = TransaccionDespacho.query.filter_by(
        id_operacion=operacion
    ).first()

    if existente:
        if (
            existente.id_despachador == id_despachador
            and existente.id_estacion == id_estacion
            and existente.litros_cargados == litros
            and existente.nro_isla == nro_isla
        ):
            return jsonify({
                "mensaje": "Esta operación ya fue registrada",
                "id_transaccion": existente.id_transaccion,
                "litros_cargados": float(existente.litros_cargados),
                "estado": existente.estado,
                "repetida": True
            }), 200

        return jsonify({
            "error": "El identificador de operación ya fue utilizado con otros datos"
        }), 409

    try:
        # 8. Buscar y bloquear el tiquete
        tiquete = TiquetDigital.query.filter_by(
            token_qr=token
        ).with_for_update().first()

        if not tiquete:
            return jsonify({
                "error": "El tiquete QR no existe"
            }), 404

        if tiquete.estado != "VIGENTE":
            return jsonify({
                "error": "El tiquete no está vigente",
                "estado": tiquete.estado
            }), 409

        # 9. Bloquear el cupo para evitar consumos simultáneos
        cupo = CupoSemanal.query.filter_by(
            id_cupo=tiquete.id_cupo
        ).with_for_update().first()

        if not cupo:
            return jsonify({
                "error": "No se encontró el cupo semanal"
            }), 404

        hoy = datetime.now(ZONA_BOLIVIA).date()

        if hoy < cupo.fecha_inicio or hoy > cupo.fecha_fin:
            tiquete.estado = "EXPIRADO"
            db.session.commit()

            return jsonify({
                "error": "El tiquete está fuera de su semana de vigencia",
                "estado": "EXPIRADO"
            }), 409

        # 10. Verificar saldo disponible
        saldo = Decimal(str(cupo.litros_disponibles))

        if saldo <= Decimal("0"):
            tiquete.estado = "AGOTADO"
            db.session.commit()

            return jsonify({
                "error": "El cupo no tiene litros disponibles",
                "estado": "AGOTADO"
            }), 409

        if litros > saldo:
            return jsonify({
                "error": "Los litros solicitados superan el saldo disponible",
                "litros_solicitados": float(litros),
                "litros_disponibles": float(saldo)
            }), 409

        # 11. Verificar vehículo y empresa
        vehiculo = db.session.get(
            Vehiculo,
            cupo.id_vehiculo
        )

        if not vehiculo or not vehiculo.activo:
            return jsonify({
                "error": "El vehículo no existe o está inactivo"
            }), 409

        empresa = db.session.get(
            Empresa,
            vehiculo.id_empresa
        )

        if not empresa or not empresa.activa:
            return jsonify({
                "error": "La empresa del vehículo está inactiva"
            }), 409

        capacidad = Decimal(str(vehiculo.capacidad_tanque))

        if litros > capacidad:
            return jsonify({
                "error": "Los litros solicitados superan la capacidad del tanque",
                "litros_solicitados": float(litros),
                "capacidad_tanque": float(capacidad)
            }), 409

        # 12. Calcular nuevo saldo
        nuevo_saldo = saldo - litros

        # 13. Crear transacción de despacho
        transaccion = TransaccionDespacho(
            id_operacion=operacion,
            id_tiquet=tiquete.id_tiquet,
            id_despachador=id_despachador,
            id_estacion=id_estacion,
            nro_isla=nro_isla,
            litros_cargados=litros,
            estado="REGISTRADA"
        )

        db.session.add(transaccion)

        # 14. Descontar litros del cupo
        cupo.litros_disponibles = nuevo_saldo

        # 15. Agotar tiquete si el saldo llega a cero
        if nuevo_saldo == Decimal("0"):
            tiquete.estado = "AGOTADO"
            tiquete.fecha_desactivacion = db.func.now()

        # 16. Guardar todo en una sola transacción
        db.session.commit()

        return jsonify({
            "mensaje": "Despacho registrado correctamente",
            "despacho": {
                "id_transaccion": transaccion.id_transaccion,
                "id_operacion": str(transaccion.id_operacion),
                "placa": vehiculo.placa,
                "empresa": empresa.nombre_empresa,
                "estacion": estacion.nombre_estacion,
                "nro_isla": transaccion.nro_isla,
                "litros_cargados": float(litros),
                "litros_disponibles": float(nuevo_saldo),
                "estado_transaccion": transaccion.estado,
                "estado_tiquete": tiquete.estado
            }
        }), 201

    except IntegrityError:
        db.session.rollback()

        # Puede ocurrir si otra solicitud registró el mismo id_operacion
        existente = TransaccionDespacho.query.filter_by(
            id_operacion=operacion
        ).first()

        if existente and existente.id_despachador == id_despachador:
            return jsonify({
                "mensaje": "Esta operación ya fue registrada",
                "id_transaccion": existente.id_transaccion,
                "litros_cargados": float(existente.litros_cargados),
                "estado": existente.estado,
                "repetida": True
            }), 200

        return jsonify({
            "error": "No fue posible registrar la operación por un conflicto de datos"
        }), 409

    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Ocurrió un error al registrar el despacho"
        }), 500


@despachos_bp.route("/<int:id_transaccion>/anular", methods=["POST"])
@jwt_required()
def anular_despacho(id_transaccion):
    datos = request.get_json(silent=True) or {}

    # 1. Verificar el rol del usuario
    claims = get_jwt()

    if claims.get("rol") != "ADMINISTRADOR":
        return jsonify({
            "error": "No tiene permisos para anular despachos"
        }), 403

    id_usuario = claims.get("id_usuario")

    if not id_usuario:
        return jsonify({
            "error": "No se pudo identificar al usuario"
        }), 401

    usuario = Usuario.query.filter_by(
        id_usuario=id_usuario,
        activo=True
    ).first()

    if not usuario:
        return jsonify({
            "error": "El usuario no existe o está inactivo"
        }), 403

    # 2. Validar el motivo
    motivo = datos.get("motivo_anulacion")

    if not isinstance(motivo, str) or not motivo.strip():
        return jsonify({
            "error": "Debe proporcionar el motivo de la anulación"
        }), 400

    motivo = motivo.strip()

    try:
        # 3. Buscar la transacción
        transaccion = TransaccionDespacho.query.filter_by(
            id_transaccion=id_transaccion
        ).first()

        if not transaccion:
            return jsonify({
                "error": "La transacción no existe"
            }), 404

        if transaccion.estado != "REGISTRADA":
            return jsonify({
                "error": "La transacción ya fue anulada",
                "estado": transaccion.estado
            }), 409

        # 4. Identificar el tiquete y el cupo
        tiquete = TiquetDigital.query.filter_by(
            id_tiquet=transaccion.id_tiquet
        ).first()

        if not tiquete:
            return jsonify({
                "error": "No se encontró el tiquete de la transacción"
            }), 404

        # Bloquear el cupo para evitar modificaciones simultáneas
        cupo = CupoSemanal.query.filter_by(
            id_cupo=tiquete.id_cupo
        ).with_for_update().first()

        if not cupo:
            return jsonify({
                "error": "No se encontró el cupo asociado"
            }), 404

        # Volver a consultar y bloquear la transacción
        transaccion = TransaccionDespacho.query.filter_by(
            id_transaccion=id_transaccion
        ).with_for_update().first()

        if transaccion.estado != "REGISTRADA":
            db.session.rollback()
            return jsonify({
                "error": "La transacción ya fue anulada",
                "estado": transaccion.estado
            }), 409

        # 5. Calcular la restauración de litros
        litros = Decimal(str(transaccion.litros_cargados))
        disponibles = Decimal(str(cupo.litros_disponibles))
        asignados = Decimal(str(cupo.litros_asignados))

        nuevo_saldo = disponibles + litros

        if nuevo_saldo > asignados:
            db.session.rollback()
            return jsonify({
                "error": "La restauración superaría los litros asignados al cupo"
            }), 409

        # 6. Restaurar los litros al cupo
        cupo.litros_disponibles = nuevo_saldo

        # 7. Marcar la transacción como anulada
        ahora = datetime.now(ZoneInfo("America/La_Paz"))

        transaccion.estado = "ANULADA"
        transaccion.id_usuario_anula = id_usuario
        transaccion.fecha_anulacion = ahora
        transaccion.motivo_anulacion = motivo

        # 8. Reactivar el tiquete agotado, si corresponde
        hoy = ahora.date()

        if (
            tiquete.estado == "AGOTADO"
            and cupo.fecha_inicio <= hoy <= cupo.fecha_fin
        ):
            otro_tiquete_vigente = TiquetDigital.query.filter(
                TiquetDigital.id_cupo == cupo.id_cupo,
                TiquetDigital.estado == "VIGENTE",
                TiquetDigital.id_tiquet != tiquete.id_tiquet
            ).first()

            if not otro_tiquete_vigente:
                tiquete.estado = "VIGENTE"
                tiquete.fecha_desactivacion = None

        # 9. Guardar todos los cambios juntos
        db.session.commit()

        return jsonify({
            "mensaje": "Despacho anulado correctamente",
            "anulacion": {
                "id_transaccion": transaccion.id_transaccion,
                "estado_transaccion": transaccion.estado,
                "litros_restaurados": float(litros),
                "litros_disponibles": float(cupo.litros_disponibles),
                "estado_tiquete": tiquete.estado,
                "id_usuario_anula": transaccion.id_usuario_anula,
                "fecha_anulacion": (
                    transaccion.fecha_anulacion.isoformat()
                ),
                "motivo_anulacion": transaccion.motivo_anulacion
            }
        }), 200

    # except SQLAlchemyError:
    #     db.session.rollback()
    #     return jsonify({
    #         "error": "Ocurrió un error en la base de datos al anular el despacho"
    #     }), 500

    # except Exception:
    #     db.session.rollback()
    #     return jsonify({
    #         "error": "Ocurrió un error inesperado al anular el despacho"
    #     }), 500
    except SQLAlchemyError as e:
        db.session.rollback()
        print("ERROR SQLAlchemy AL ANULAR DESPACHO:", repr(e))
        traceback.print_exc()

        return jsonify({
            "error": "Ocurrió un error en la base de datos al anular el despacho"
        }), 500

    except Exception as e:
        db.session.rollback()
        print("ERROR INESPERADO AL ANULAR DESPACHO:", repr(e))
        traceback.print_exc()

        return jsonify({
            "error": "Ocurrió un error inesperado al anular el despacho",
            "detalle": str(e)
        }), 500


@despachos_bp.route("/historial", methods=["GET"])
@jwt_required()
def obtener_historial_despachos():
    """
    Historial de despachos.

    ADMINISTRADOR:
        Puede consultar todos los despachos.

    TRANSPORTISTA:
        Solo puede consultar despachos de sus vehículos
        con asignación activa.
    """

    try:
        datos_jwt = get_jwt()

        id_usuario = datos_jwt.get("id_usuario")
        rol = datos_jwt.get("rol")

        if rol not in ["ADMINISTRADOR", "TRANSPORTISTA"]:
            return jsonify({
                "error": "No tienes permiso para consultar el historial"
            }), 403

        usuario = Usuario.query.filter_by(
            id_usuario=id_usuario,
            activo=True
        ).first()

        if not usuario:
            return jsonify({
                "error": "El usuario no existe o está inactivo"
            }), 403

        # Consulta principal con las relaciones necesarias.
        consulta = (
            db.session.query(
                TransaccionDespacho,
                TiquetDigital,
                CupoSemanal,
                Vehiculo,
                Empresa,
                Estacion,
            )
            .join(
                TiquetDigital,
                TransaccionDespacho.id_tiquet == TiquetDigital.id_tiquet
            )
            .join(
                CupoSemanal,
                TiquetDigital.id_cupo == CupoSemanal.id_cupo
            )
            .join(
                Vehiculo,
                CupoSemanal.id_vehiculo == Vehiculo.id_vehiculo
            )
            .join(
                Empresa,
                Vehiculo.id_empresa == Empresa.id_empresa
            )
            .join(
                Estacion,
                TransaccionDespacho.id_estacion == Estacion.id_estacion
            )
        )

        # Restricción de acceso para transportistas.
        if rol == "TRANSPORTISTA":
            consulta = (
                consulta
                .join(
                    AsignacionVehiculo,
                    AsignacionVehiculo.id_vehiculo
                    == Vehiculo.id_vehiculo
                )
                .filter(
                    AsignacionVehiculo.id_usuario == id_usuario,
                    AsignacionVehiculo.activa.is_(True)
                )
            )

        # Filtro por fecha inicial.
        fecha_desde = request.args.get("fecha_desde")

        if fecha_desde:
            try:
                fecha_desde = date.fromisoformat(fecha_desde)
            except ValueError:
                return jsonify({
                    "error": "fecha_desde debe tener formato YYYY-MM-DD"
                }), 400

            inicio_dia = datetime.combine(
                fecha_desde,
                datetime.min.time(),
                tzinfo=ZoneInfo("America/La_Paz")
            )

            consulta = consulta.filter(
                TransaccionDespacho.fecha_hora >= inicio_dia
            )

        # Filtro por fecha final.
        fecha_hasta = request.args.get("fecha_hasta")

        if fecha_hasta:
            try:
                fecha_hasta = date.fromisoformat(fecha_hasta)
            except ValueError:
                return jsonify({
                    "error": "fecha_hasta debe tener formato YYYY-MM-DD"
                }), 400

            fin_dia = datetime.combine(
                fecha_hasta + timedelta(days=1),
                datetime.min.time(),
                tzinfo=ZoneInfo("America/La_Paz")
            )

            # Se utiliza límite exclusivo para incluir todo el día.
            consulta = consulta.filter(
                TransaccionDespacho.fecha_hora < fin_dia
            )

        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            return jsonify({
                "error": "La fecha inicial no puede ser posterior a la fecha final"
            }), 400

        # Filtro por placa.
        placa = request.args.get("placa")

        if placa:
            consulta = consulta.filter(
                Vehiculo.placa.ilike(f"%{placa.strip()}%")
            )
                
        # Filtro por empresa.
        id_empresa = request.args.get("id_empresa")

        if id_empresa:
            try:
                id_empresa = int(id_empresa)
            except (TypeError, ValueError):
                return jsonify({
                    "error": "id_empresa debe ser un número entero"
                }), 400

            if id_empresa <= 0:
                return jsonify({
                    "error": "id_empresa debe ser mayor a cero"
                }), 400

            consulta = consulta.filter(
                Empresa.id_empresa == id_empresa
            )


        # Filtro por estación.
        id_estacion = request.args.get("id_estacion")

        if id_estacion:
            try:
                id_estacion = int(id_estacion)
            except ValueError:
                return jsonify({
                    "error": "id_estacion debe ser un número entero"
                }), 400

            consulta = consulta.filter(
                TransaccionDespacho.id_estacion == id_estacion
            )

        # Filtro por estado.
        estado = request.args.get("estado")

        if estado:
            estado = estado.strip().upper()

            if estado not in ["REGISTRADA", "ANULADA"]:
                return jsonify({
                    "error": "El estado debe ser REGISTRADA o ANULADA"
                }), 400

            consulta = consulta.filter(
                TransaccionDespacho.estado == estado
            )

        # Ordenar del despacho más reciente al más antiguo.
        resultados = consulta.order_by(
            TransaccionDespacho.fecha_hora.desc(),
            TransaccionDespacho.id_transaccion.desc()
        ).all()

        historial = []

        for transaccion, tiquet, cupo, vehiculo, empresa, estacion in resultados:

            historial.append({
                "id_transaccion": transaccion.id_transaccion,
                "id_operacion": str(transaccion.id_operacion),
                "fecha_hora": transaccion.fecha_hora.isoformat(),

                "placa": vehiculo.placa,
                "modelo": vehiculo.modelo,

                "id_empresa": empresa.id_empresa,
                "nombre_empresa": empresa.nombre_empresa,

                "id_estacion": estacion.id_estacion,
                "nombre_estacion": estacion.nombre_estacion,

                "nro_isla": transaccion.nro_isla,
                "litros_cargados": float(transaccion.litros_cargados),

                "estado": transaccion.estado,
                "motivo_anulacion": transaccion.motivo_anulacion,
                "fecha_anulacion": (
                    transaccion.fecha_anulacion.isoformat()
                    if transaccion.fecha_anulacion
                    else None
                )
            })

        return jsonify({
            "mensaje": "Historial de despachos obtenido correctamente",
            "total": len(historial),
            "historial": historial
        }), 200

    except Exception as e:
        db.session.rollback()
        print("ERROR AL OBTENER HISTORIAL:", repr(e))

        return jsonify({
            "error": "Ocurrió un error al consultar el historial"
        }), 500
    

@despachos_bp.route("/historial/exportar-csv", methods=["GET"])
@jwt_required()
def exportar_historial_csv():

    try:
        datos_jwt = get_jwt()

        id_usuario = datos_jwt.get("id_usuario")
        rol = datos_jwt.get("rol")

        # Solo el administrador puede exportar.
        if rol != "ADMINISTRADOR":
            return jsonify({
                "error": "No tienes permiso para exportar el historial"
            }), 403

        usuario = Usuario.query.filter_by(
            id_usuario=id_usuario,
            activo=True
        ).first()

        if not usuario:
            return jsonify({
                "error": "El usuario no existe o está inactivo"
            }), 403

        consulta = (
            db.session.query(
                TransaccionDespacho,
                Vehiculo,
                Empresa,
                Estacion,
            )
            .join(
                TiquetDigital,
                TransaccionDespacho.id_tiquet == TiquetDigital.id_tiquet
            )
            .join(
                CupoSemanal,
                TiquetDigital.id_cupo == CupoSemanal.id_cupo
            )
            .join(
                Vehiculo,
                CupoSemanal.id_vehiculo == Vehiculo.id_vehiculo
            )
            .join(
                Empresa,
                Vehiculo.id_empresa == Empresa.id_empresa
            )
            .join(
                Estacion,
                TransaccionDespacho.id_estacion == Estacion.id_estacion
            )
        )

        # Filtro por fecha inicial.
        fecha_desde = request.args.get("fecha_desde")

        if fecha_desde:
            try:
                fecha_desde = date.fromisoformat(fecha_desde)
            except ValueError:
                return jsonify({
                    "error": "fecha_desde debe tener formato YYYY-MM-DD"
                }), 400

            inicio_dia = datetime.combine(
                fecha_desde,
                datetime.min.time(),
                tzinfo=ZoneInfo("America/La_Paz")
            )

            consulta = consulta.filter(
                TransaccionDespacho.fecha_hora >= inicio_dia
            )

        # Filtro por fecha final.
        fecha_hasta = request.args.get("fecha_hasta")

        if fecha_hasta:
            try:
                fecha_hasta = date.fromisoformat(fecha_hasta)
            except ValueError:
                return jsonify({
                    "error": "fecha_hasta debe tener formato YYYY-MM-DD"
                }), 400

            fin_dia = datetime.combine(
                fecha_hasta + timedelta(days=1),
                datetime.min.time(),
                tzinfo=ZoneInfo("America/La_Paz")
            )

            consulta = consulta.filter(
                TransaccionDespacho.fecha_hora < fin_dia
            )

        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            return jsonify({
                "error": "La fecha inicial no puede ser posterior a la fecha final"
            }), 400

        # Filtro por placa.
        placa = request.args.get("placa")

        if placa:
            consulta = consulta.filter(
                Vehiculo.placa.ilike(f"%{placa.strip()}%")
            )
        
        # Filtro por empresa.
        id_empresa = request.args.get("id_empresa")

        if id_empresa:
            try:
                id_empresa = int(id_empresa)
            except (TypeError, ValueError):
                return jsonify({
                    "error": "id_empresa debe ser un número entero"
                }), 400

            if id_empresa <= 0:
                return jsonify({
                    "error": "id_empresa debe ser mayor a cero"
                }), 400

            consulta = consulta.filter(
                Empresa.id_empresa == id_empresa
            )


        # Filtro por estación.
        id_estacion = request.args.get("id_estacion")

        if id_estacion:
            try:
                id_estacion = int(id_estacion)
            except ValueError:
                return jsonify({
                    "error": "id_estacion debe ser un número entero"
                }), 400

            consulta = consulta.filter(
                TransaccionDespacho.id_estacion == id_estacion
            )

        # Filtro por estado.
        estado = request.args.get("estado")

        if estado:
            estado = estado.strip().upper()

            if estado not in ["REGISTRADA", "ANULADA"]:
                return jsonify({
                    "error": "El estado debe ser REGISTRADA o ANULADA"
                }), 400

            consulta = consulta.filter(
                TransaccionDespacho.estado == estado
            )

        resultados = consulta.order_by(
            TransaccionDespacho.fecha_hora.desc(),
            TransaccionDespacho.id_transaccion.desc()
        ).all()

        # Preparar archivo CSV.
        salida = StringIO(newline="")

        escritor = csv.writer(salida, delimiter=";")

        escritor.writerow([
            "Nro. Transacción",
            "ID Operación",
            "Fecha y hora",
            "Placa",
            "Modelo",
            "Empresa",
            "Estación",
            "Nro. Isla",
            "Litros cargados",
            "Estado",
            "Fecha de anulación",
            "Motivo de anulación"
        ])

        for transaccion, vehiculo, empresa, estacion in resultados:

            escritor.writerow([
                transaccion.id_transaccion,
                str(transaccion.id_operacion),
                transaccion.fecha_hora.isoformat(),
                vehiculo.placa,
                vehiculo.modelo or "",
                empresa.nombre_empresa,
                estacion.nombre_estacion,
                transaccion.nro_isla,
                str(transaccion.litros_cargados),
                transaccion.estado,
                (
                    transaccion.fecha_anulacion.isoformat()
                    if transaccion.fecha_anulacion
                    else ""
                ),
                transaccion.motivo_anulacion or ""
            ])

        # BOM para facilitar la lectura de caracteres especiales en Excel.
        contenido = "\ufeff" + salida.getvalue()
        salida.close()

        return Response(
            contenido,
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition":
                    'attachment; filename="historial_despachos.csv"'
            }
        )

    except Exception as e:
        db.session.rollback()
        print("ERROR AL EXPORTAR HISTORIAL:", repr(e))

        return jsonify({
            "error": "Ocurrió un error al exportar el historial"
        }), 500
