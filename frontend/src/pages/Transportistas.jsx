
import { useEffect, useMemo, useState } from "react";
import {Plus, Search, Pencil, Power, Truck, X, UserRound, Building2, ChevronDown} from "lucide-react";
import AdminLayout from "../layouts/AdminLayout";
import api from "../services/api";
import "../estilos/trasportistas.css";
import "../estilos/admin-modules.css";


function Transportistas() {
    const [transportistas, setTransportistas] = useState([]);
    const [empresas, setEmpresas] = useState([]);
    const [vehiculos, setVehiculos] = useState([]);
    const [asignaciones, setAsignaciones] = useState([]);

    const [busqueda, setBusqueda] = useState("");
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");
    const [guardando, setGuardando] = useState(false);

    const [modal, setModal] = useState("");
    const [seleccionado, setSeleccionado] = useState(null);

    const formularioInicial = {
        nombre: "",
        apellido: "",
        ci: "",
        telefono: "",
        email: "",
        password: "",
        id_empresa: "",
    };

    const [formulario, setFormulario] = useState(formularioInicial);
    const [idVehiculo, setIdVehiculo] = useState("");

    const cargarDatos = async () => {
        setCargando(true);
        setError("");

        try {
            const [usuariosRes, empresasRes, vehiculosRes, asignacionesRes] =
                await Promise.all([
                    api.get("/usuarios"),
                    api.get("/empresas"),
                    api.get("/vehiculos"),
                    api.get("/asignaciones"),
                ]);

            setTransportistas(
                usuariosRes.data.usuarios.filter(
                    (u) => u.rol === "TRANSPORTISTA"
                )
            );

            setEmpresas(empresasRes.data.empresas);
            setVehiculos(vehiculosRes.data.vehiculos);
            setAsignaciones(asignacionesRes.data.asignaciones);
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudieron cargar los datos."
            );
        } finally {
            setCargando(false);
        }
    };

    useEffect(() => {
        cargarDatos();
    }, []);

    const filtrados = useMemo(() => {
        const termino = busqueda.toLowerCase().trim();

        return transportistas.filter((t) => {
            const empresa = empresas.find(
                (e) => e.id_empresa === t.id_empresa
            );

            const texto = [
                t.nombre,
                t.apellido,
                t.ci,
                t.telefono,
                t.email,
                empresa?.nombre_empresa,
            ].join(" ").toLowerCase();

            return texto.includes(termino);
        });
    }, [transportistas, empresas, busqueda]);

    const cambiarCampo = (e) => {
        setFormulario({
            ...formulario,
            [e.target.name]: e.target.value,
        });
    };

    const abrirRegistro = () => {
        setSeleccionado(null);
        setFormulario(formularioInicial);
        setModal("formulario");
    };

    const abrirEdicion = (transportista) => {
        setSeleccionado(transportista);
        setFormulario({
            nombre: transportista.nombre || "",
            apellido: transportista.apellido || "",
            ci: transportista.ci || "",
            telefono: transportista.telefono || "",
            email: transportista.email || "",
            password: "",
            id_empresa: String(transportista.id_empresa || ""),
        });
        setModal("formulario");
    };

    const guardarTransportista = async (e) => {
        e.preventDefault();
        setGuardando(true);
        setError("");

        try {
            const datos = {
                nombre: formulario.nombre.trim(),
                apellido: formulario.apellido.trim(),
                ci: formulario.ci.trim(),
                telefono: formulario.telefono.trim(),
                email: formulario.email.trim(),
                id_empresa: Number(formulario.id_empresa),
            };

            if (seleccionado) {
                await api.patch(
                    `/usuarios/${seleccionado.id_usuario}`,
                    datos
                );
            } else {
                await api.post("/usuarios", {
                    ...datos,
                    password: formulario.password,
                    rol: "TRANSPORTISTA",
                });
            }

            setModal("");
            await cargarDatos();
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudo guardar el transportista."
            );
        } finally {
            setGuardando(false);
        }
    };

    const cambiarEstado = async (transportista) => {
        const accion = transportista.activo ? "desactivar" : "activar";

        if (!window.confirm(
            `¿Deseas ${accion} a ${transportista.nombre} ${transportista.apellido}?`
        )) return;

        try {
            await api.patch(
                `/usuarios/${transportista.id_usuario}/estado`,
                { activo: !transportista.activo }
            );

            await cargarDatos();
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudo cambiar el estado."
            );
        }
    };

    const abrirAsignaciones = (transportista) => {
        setSeleccionado(transportista);
        setIdVehiculo("");
        setModal("asignaciones");
    };

    const asignacionesActuales = asignaciones.filter(
        (a) =>
            a.id_usuario === seleccionado?.id_usuario &&
            a.activa
    );

    const vehiculosDisponibles = vehiculos.filter(
        (v) =>
            v.activo &&
            v.id_empresa === seleccionado?.id_empresa &&
            !asignacionesActuales.some(
                (a) => a.id_vehiculo === v.id_vehiculo
            )
    );

    const asignarVehiculo = async (e) => {
        e.preventDefault();

        if (!idVehiculo) return;

        setGuardando(true);
        setError("");

        try {
            await api.post("/asignaciones", {
                id_usuario: seleccionado.id_usuario,
                id_vehiculo: Number(idVehiculo),
            });

            await cargarDatos();
            setIdVehiculo("");
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudo asignar el vehículo."
            );
        } finally {
            setGuardando(false);
        }
    };

    const desasignarVehiculo = async (asignacion) => {
        if (!window.confirm(
            `¿Deseas desasignar el vehículo ${asignacion.placa}?`
        )) return;

        try {
            await api.patch(
                `/asignaciones/${asignacion.id_asignacion}/estado`,
                { activa: false }
            );

            await cargarDatos();
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudo desasignar el vehículo."
            );
        }
    };

    return (
        <AdminLayout>
            <div className="empresas-pagina">
                <div className="empresas-encabezado">
                    <div>
                        <h1>Transportistas</h1>
                        <p>
                            Administra transportistas y sus vehículos asignados.
                        </p>
                    </div>

                    <button
                        className="btn-nueva-empresa"
                        onClick={abrirRegistro}
                    >
                        <Plus size={18} />
                        Nuevo transportista
                    </button>
                </div>

                {error && (
                    <div className="mensaje-error">
                        {error}
                        <button onClick={() => setError("")}>
                            <X size={16} />
                        </button>
                    </div>
                )}

                <div className="empresas-busqueda">
                    <Search size={19} />
                    <input
                        type="text"
                        placeholder="Buscar por nombre, CI, teléfono o empresa..."
                        value={busqueda}
                        onChange={(e) => setBusqueda(e.target.value)}
                    />
                </div>

                <div className="empresas-resumen">
                    <span>
                        Total de transportistas: <strong>{transportistas.length}</strong>
                    </span>
                    <span>
                        Activos: <strong>
                            {transportistas.filter((t) => t.activo).length}
                        </strong>
                    </span>
                </div>

                <div className="tabla-empresas-contenedor">
                    {cargando ? (
                        <p className="mensaje-cargando">Cargando transportistas...</p>
                    ) : (
                        <table className="tabla-empresas">
                            <thead>
                                <tr>
                                    <th>Transportista</th>
                                    <th>CI</th>
                                    <th>Teléfono</th>
                                    <th>Empresa</th>
                                    <th>Vehículos</th>
                                    <th>Estado</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>

                            <tbody>
                                {filtrados.map((t) => {
                                    const empresa = empresas.find(
                                        (e) => e.id_empresa === t.id_empresa
                                    );

                                    const cantidad = asignaciones.filter(
                                        (a) =>
                                            a.id_usuario === t.id_usuario &&
                                            a.activa
                                    ).length;

                                    return (
                                        <tr key={t.id_usuario}>
                                            <td>
                                                <strong>{t.nombre} {t.apellido}</strong>
                                                <small className="texto-secundario">
                                                    {t.email}
                                                </small>
                                            </td>
                                            <td>{t.ci || "—"}</td>
                                            <td>{t.telefono || "—"}</td>
                                            <td>{empresa?.nombre_empresa || "—"}</td>
                                            <td>{cantidad}</td>
                                            <td>
                                                <span className={
                                                    t.activo
                                                        ? "estado-activo"
                                                        : "estado-inactivo"
                                                }>
                                                    {t.activo ? "Activo" : "Inactivo"}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="acciones-empresa">
                                                    <button
                                                        className="btn-editar-empresa"
                                                        title="Editar"
                                                        onClick={() => abrirEdicion(t)}
                                                    >
                                                        <Pencil size={16} />
                                                    </button>

                                                    <button
                                                        className="btn-editar-empresa"
                                                        title="Gestionar vehículos"
                                                        onClick={() => abrirAsignaciones(t)}
                                                    >
                                                        <Truck size={17} />
                                                    </button>

                                                    <button
                                                        className={
                                                            t.activo
                                                                ? "btn-desactivar-empresa"
                                                                : "btn-activar-empresa"
                                                        }
                                                        title={t.activo ? "Desactivar" : "Activar"}
                                                        onClick={() => cambiarEstado(t)}
                                                    >
                                                        <Power size={16} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}

                                {!filtrados.length && (
                                    <tr>
                                        <td colSpan="7" className="tabla-vacia">
                                            No se encontraron transportistas.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {modal === "formulario" && (
                <div className="modal-fondo">
                    <div className="modal-empresa">
                        <div className="modal-empresa-encabezado">
                            <div>
                                <h2>
                                    {seleccionado
                                        ? "Editar transportista"
                                        : "Registrar transportista"}
                                </h2>
                                <p>Completa los datos del transportista.</p>
                            </div>
                            <button
                                className="btn-cerrar-modal"
                                onClick={() => setModal("")}
                                type="button"
                            >
                                <X />
                            </button>
                        </div>

                        <form onSubmit={guardarTransportista}>
                            <div className="formulario-empresa-grid">
                                <div className="campo-empresa">
                                    <label>Nombre *</label>
                                    <input
                                        name="nombre"
                                        value={formulario.nombre}
                                        onChange={cambiarCampo}
                                        maxLength="100"
                                        required
                                    />
                                </div>

                                <div className="campo-empresa">
                                    <label>Apellido *</label>
                                    <input
                                        name="apellido"
                                        value={formulario.apellido}
                                        onChange={cambiarCampo}
                                        maxLength="150"
                                        required
                                    />
                                </div>

                                <div className="campo-empresa">
                                    <label>CI *</label>
                                    <input
                                        name="ci"
                                        value={formulario.ci}
                                        onChange={cambiarCampo}
                                        required
                                    />
                                </div>

                                <div className="campo-empresa">
                                    <label>Teléfono *</label>
                                    <input
                                        name="telefono"
                                        value={formulario.telefono}
                                        onChange={cambiarCampo}
                                        maxLength="30"
                                        required
                                    />
                                </div>

                                <div className="campo-empresa">
                                    <label>Correo electrónico *</label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={formulario.email}
                                        onChange={cambiarCampo}
                                        required
                                    />
                                </div>

                                {!seleccionado && (
                                    <div className="campo-empresa">
                                        <label>Contraseña *</label>
                                        <input
                                            type="password"
                                            name="password"
                                            value={formulario.password}
                                            onChange={cambiarCampo}
                                            minLength="12"
                                            required
                                        />
                                    </div>
                                )}

                                <div className="campo-empresa campo-completo">
                                    <label>Empresa *</label>
                                    <select
                                        name="id_empresa"
                                        value={formulario.id_empresa}
                                        onChange={cambiarCampo}
                                        required
                                    >
                                        <option value="">Seleccionar empresa</option>
                                        {empresas
                                            .filter((e) => e.activa)
                                            .map((e) => (
                                                <option
                                                    key={e.id_empresa}
                                                    value={e.id_empresa}
                                                >
                                                    {e.nombre_empresa}
                                                </option>
                                            ))}
                                    </select>
                                </div>
                            </div>

                            <div className="acciones-formulario">
                                <button
                                    type="button"
                                    className="btn-cancelar"
                                    onClick={() => setModal("")}
                                >
                                    Cancelar
                                </button>

                                <button
                                    type="submit"
                                    className="btn-guardar"
                                    disabled={guardando}
                                >
                                    {guardando
                                        ? "Guardando..."
                                        : seleccionado
                                            ? "Guardar cambios"
                                            : "Registrar transportista"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {modal === "asignaciones" && seleccionado && (
                <div className="modal-fondo">
                    <div className="modal-empresa">
                        <div className="modal-empresa-encabezado">
                            <div>
                                <h2>Vehículos asignados</h2>
                                <p>
                                    {seleccionado.nombre} {seleccionado.apellido}
                                </p>
                            </div>
                            <button
                                className="btn-cerrar-modal"
                                onClick={() => setModal("")}
                                type="button"
                            >
                                <X />
                            </button>
                        </div>

                        <form
                            onSubmit={asignarVehiculo}
                            className="asignacion-formulario"
                        >
                            <div className="campo-empresa">
                                <label>Seleccionar vehículo disponible</label>
                                <select
                                    value={idVehiculo}
                                    onChange={(e) => setIdVehiculo(e.target.value)}
                                    required
                                >
                                    <option value="">Seleccionar vehículo</option>
                                    {vehiculosDisponibles.map((v) => (
                                        <option
                                            key={v.id_vehiculo}
                                            value={v.id_vehiculo}
                                        >
                                            {v.placa} {v.modelo ? `- ${v.modelo}` : ""}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <button
                                className="btn-guardar"
                                type="submit"
                                disabled={guardando || !idVehiculo}
                            >
                                <Plus size={17} />
                                Asignar vehículo
                            </button>
                        </form>

                        <div className="lista-asignaciones">
                            <h3>Asignaciones activas</h3>

                            {asignacionesActuales.length === 0 ? (
                                <p>No tiene vehículos asignados.</p>
                            ) : (
                                asignacionesActuales.map((a) => (
                                    <div
                                        className="asignacion-item"
                                        key={a.id_asignacion}
                                    >
                                        <div>
                                            <Truck size={19} />
                                            <strong>{a.placa}</strong>
                                        </div>
                                        <button
                                            className="btn-desasignar"
                                            onClick={() => desasignarVehiculo(a)}
                                        >
                                            Desasignar
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="acciones-formulario">
                            <button
                                className="btn-cancelar"
                                onClick={() => setModal("")}
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </AdminLayout>
    );
}

export default Transportistas;
