import uuid

from sqlalchemy import (
    CheckConstraint,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from extensions import db


class Rol(db.Model):
    __tablename__ = "rol"

    id_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(30), unique=True, nullable=False)


class Empresa(db.Model):
    __tablename__ = "empresa"

    id_empresa = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(150), nullable=False)
    nit = db.Column(db.String(30), unique=True, nullable=False)
    telefono = db.Column(db.String(30))
    activa = db.Column(db.Boolean, nullable=False, default=True)


class Estacion(db.Model):
    __tablename__ = "estacion"

    id_estacion = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True, nullable=False)
    nombre_estacion = db.Column(db.String(150), nullable=False)
    direccion = db.Column(db.String(250))
    ciudad = db.Column(db.String(100))
    activa = db.Column(db.Boolean, nullable=False, default=True)


class Usuario(db.Model):
    __tablename__ = "usuario"

    id_usuario = db.Column(db.Integer, primary_key=True)

    id_rol = db.Column(
        db.Integer,
        db.ForeignKey("rol.id_rol"),
        nullable=False,
    )

    id_empresa = db.Column(
        db.Integer,
        db.ForeignKey("empresa.id_empresa"),
        nullable=True,
    )

    id_estacion = db.Column(
        db.Integer,
        db.ForeignKey("estacion.id_estacion"),
        nullable=True,
    )

    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(150), nullable=False)

    # La CI será obligatoria para transportistas
    # y única cuando se proporcione.
    ci = db.Column(db.String(30), unique=True, nullable=True)

    # Obligatorio para transportistas; validación en la API.
    telefono = db.Column(db.String(30), nullable=True)

    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)

class Vehiculo(db.Model):
    __tablename__ = "vehiculo"

    id_vehiculo = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(
        db.Integer, db.ForeignKey("empresa.id_empresa"), nullable=False
    )
    placa = db.Column(db.String(20), unique=True, nullable=False)
    modelo = db.Column(db.String(100))
    capacidad_tanque = db.Column(db.Numeric(10, 2), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint(
            "capacidad_tanque > 0",
            name="ck_vehiculo_capacidad_positiva",
        ),
    )


class AsignacionVehiculo(db.Model):
    __tablename__ = "asignacion_vehiculo"

    id_asignacion = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    id_vehiculo = db.Column(
        db.Integer, db.ForeignKey("vehiculo.id_vehiculo"), nullable=False
    )
    activa = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "id_usuario", "id_vehiculo",
            name="uq_asignacion_usuario_vehiculo",
        ),
    )


class CupoSemanal(db.Model):
    __tablename__ = "cupo_semanal"

    id_cupo = db.Column(db.Integer, primary_key=True)
    id_vehiculo = db.Column(
        db.Integer, db.ForeignKey("vehiculo.id_vehiculo"), nullable=False
    )
    id_usuario_asigna = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    litros_asignados = db.Column(db.Numeric(10, 2), nullable=False)
    litros_disponibles = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    fecha_asignacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "id_vehiculo", "fecha_inicio",
            name="uq_cupo_vehiculo_semana",
        ),
        CheckConstraint(
            "litros_asignados > 0",
            name="ck_cupo_litros_asignados",
        ),
        CheckConstraint(
            "litros_disponibles >= 0 "
            "AND litros_disponibles <= litros_asignados",
            name="ck_cupo_litros_disponibles",
        ),
        CheckConstraint(
            "fecha_fin >= fecha_inicio",
            name="ck_cupo_fechas",
        ),
    )


class TiquetDigital(db.Model):
    __tablename__ = "tiquet_digital"

    id_tiquet = db.Column(db.Integer, primary_key=True)
    id_cupo = db.Column(
        db.Integer, db.ForeignKey("cupo_semanal.id_cupo"), nullable=False
    )
    id_usuario_genera = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    token_qr = db.Column(UUID(as_uuid=True), unique=True, nullable=False,
                         default=uuid.uuid4)
    estado = db.Column(db.String(20), nullable=False, default="VIGENTE")
    fecha_generacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    fecha_desactivacion = db.Column(db.DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "estado IN ('VIGENTE', 'AGOTADO', 'EXPIRADO', 'ANULADO')",
            name="ck_tiquet_estado",
        ),
        Index(
            "uq_tiquet_vigente_por_cupo",
            "id_cupo",
            unique=True,
            postgresql_where=text("estado = 'VIGENTE'"),
        ),
    )


class TransaccionDespacho(db.Model):
    __tablename__ = "transaccion_despacho"

    id_transaccion = db.Column(db.Integer, primary_key=True)
    id_operacion = db.Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    id_tiquet = db.Column(
        db.Integer, db.ForeignKey("tiquet_digital.id_tiquet"), nullable=False
    )
    id_despachador = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    id_estacion = db.Column(
        db.Integer, db.ForeignKey("estacion.id_estacion"), nullable=False
    )
    nro_isla = db.Column(db.String(20), nullable=False)
    litros_cargados = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_hora = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    estado = db.Column(db.String(20), nullable=False, default="REGISTRADA")
    id_usuario_anula = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=True
    )
    fecha_anulacion = db.Column(db.DateTime(timezone=True))
    motivo_anulacion = db.Column(db.Text)

    __table_args__ = (
        CheckConstraint(
            "litros_cargados > 0",
            name="ck_despacho_litros_positivos",
        ),
        CheckConstraint(
            "estado IN ('REGISTRADA', 'ANULADA')",
            name="ck_despacho_estado",
        ),
    )