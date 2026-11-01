from getpass import getpass

from app import app
from extensions import db, bcrypt
from models import Rol, Usuario


ROLES = [
    "ADMINISTRADOR",
    "TRANSPORTISTA",
    "DESPACHADOR",
]


with app.app_context():
    # Crear los roles que aún no existan.
    for nombre_rol in ROLES:
        existente = Rol.query.filter_by(
            nombre_rol=nombre_rol
        ).first()

        if existente is None:
            db.session.add(Rol(nombre_rol=nombre_rol))

    db.session.commit()

    rol_admin = Rol.query.filter_by(
        nombre_rol="ADMINISTRADOR"
    ).first()

    print("\nInicialización de seguridad SIGODIESEL B2B")

    administrador = Usuario.query.filter_by(
        id_rol=rol_admin.id_rol
    ).first()

    if administrador:
        print(
            "Ya existe un usuario administrador. "
            "No se creó otro."
        )
    else:
        nombre = input("Nombre del administrador: ").strip()
        apellido = input("Apellido del administrador: ").strip()
        email = input("Correo del administrador: ").strip().lower()
        password = getpass("Contraseña inicial: ")
        confirmar = getpass("Confirma la contraseña: ")

        if not all([nombre, apellido, email, password]):
            raise ValueError(
                "Nombre, apellido, correo y contraseña son obligatorios."
            )

        if password != confirmar:
            raise ValueError("Las contraseñas no coinciden.")

        if len(password) < 12:
            raise ValueError(
                "Usa una contraseña de al menos 12 caracteres."
            )

        if Usuario.query.filter_by(email=email).first():
            raise ValueError(
                "Ese correo ya está registrado."
            )

        usuario = Usuario(
            id_rol=rol_admin.id_rol,
            nombre=nombre,
            apellido=apellido,
            email=email,
            password_hash=bcrypt.generate_password_hash(
                password
            ).decode("utf-8"),
            activo=True,
        )

        db.session.add(usuario)
        db.session.commit()

        print("Administrador creado correctamente.")

    print("\nRoles registrados:")
    for rol in Rol.query.order_by(Rol.id_rol).all():
        print(f"- {rol.nombre_rol}")