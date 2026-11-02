
import { useEffect, useState } from "react";
import { Plus, Search, X, Fuel, CalendarDays, Truck } from "lucide-react";
import AdminLayout from "../layouts/AdminLayout";
import api from "../services/api";
import "../estilos/cupos.css";
import "../estilos/admin-modules.css";

function obtenerFechaLocal() {
    const hoy = new Date();
    const anio = hoy.getFullYear();
    const mes = String(hoy.getMonth() + 1).padStart(2, "0");
    const dia = String(hoy.getDate()).padStart(2, "0");

    return `${anio}-${mes}-${dia}`;
}

function formatearFecha(fecha) {
    if (!fecha) return "-";

    const [anio, mes, dia] = fecha.split("-");
    return `${dia}/${mes}/${anio}`;
}

function Cupos() {
    const [cupos, setCupos] = useState([]);
    const [vehiculos, setVehiculos] = useState([]);

    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");
    const [mensaje, setMensaje] = useState("");

    const [filtroVehiculo, setFiltroVehiculo] = useState("");
    const [filtroFecha, setFiltroFecha] = useState("");

    const [modalAbierto, setModalAbierto] = useState(false);
    const [guardando, setGuardando] = useState(false);

    const [formulario, setFormulario] = useState({
        id_vehiculo: "",
        litros_asignados: "",
        fecha_inicio: obtenerFechaLocal(),
    });

    const cargarVehiculos = async () => {
        const respuesta = await api.get("/vehiculos");
        setVehiculos(respuesta.data.vehiculos || []);
    };

    const cargarCupos = async () => {
        try {
            setCargando(true);
            setError("");

            const parametros = {};

            if (filtroVehiculo) {
                parametros.id_vehiculo = filtroVehiculo;
            }

            if (filtroFecha) {
                parametros.fecha = filtroFecha;
            }

            const respuesta = await api.get("/cupos", {
                params: parametros,
            });

            setCupos(respuesta.data);
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudieron cargar los cupos."
            );
        } finally {
            setCargando(false);
        }
    };

    useEffect(() => {
        const inicializar = async () => {
            try {
                await Promise.all([
                    cargarVehiculos(),
                    cargarCupos(),
                ]);
            } catch (err) {
                setError(
                    err.response?.data?.error ||
                    "No se pudieron cargar los datos."
                );
            }
        };

        inicializar();
    }, []);

    const buscarCupos = async (e) => {
        e.preventDefault();
        await cargarCupos();
    };

    const limpiarFiltros = async () => {
        setFiltroVehiculo("");
        setFiltroFecha("");

        try {
            setCargando(true);
            setError("");

            const respuesta = await api.get("/cupos");
            setCupos(respuesta.data);
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudieron cargar los cupos."
            );
        } finally {
            setCargando(false);
        }
    };

    const cambiarCampo = (e) => {
        const { name, value } = e.target;

        setFormulario((actual) => ({
            ...actual,
            [name]: value,
        }));
    };

    const registrarCupo = async (e) => {
        e.preventDefault();

        try {
            setGuardando(true);
            setError("");
            setMensaje("");

            await api.post("/cupos", {
                id_vehiculo: Number(formulario.id_vehiculo),
                litros_asignados: Number(formulario.litros_asignados),
                fecha_inicio: formulario.fecha_inicio,
            });

            setMensaje("Cupo semanal registrado correctamente.");

            setFormulario({
                id_vehiculo: "",
                litros_asignados: "",
                fecha_inicio: obtenerFechaLocal(),
            });

            setModalAbierto(false);

            const respuesta = await api.get("/cupos");
            setCupos(respuesta.data);
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudo registrar el cupo."
            );
        } finally {
            setGuardando(false);
        }
    };

    const obtenerPlaca = (idVehiculo) => {
        const vehiculo = vehiculos.find(
            (item) => item.id_vehiculo === idVehiculo
        );

        return vehiculo?.placa || `Vehículo #${idVehiculo}`;
    };

    const totalAsignado = cupos.reduce(
        (total, cupo) => total + Number(cupo.litros_asignados),
        0
    );

    const totalDisponible = cupos.reduce(
        (total, cupo) => total + Number(cupo.litros_disponibles),
        0
    );

    return (
        <AdminLayout>
            <div className="pagina-empresas">
                <div className="encabezado-modulo">
                    <div>
                        <h1>Cupos semanales</h1>
                        <p>
                            Administración de litros asignados a los vehículos
                            de transporte.
                        </p>
                    </div>

                    <button
                        className="btn-principal"
                        onClick={() => {
                            setError("");
                            setMensaje("");
                            setModalAbierto(true);
                        }}
                    >
                        <Plus size={18} />
                        Asignar cupo
                    </button>
                </div>

                {mensaje && (
                    <div className="mensaje-exito">{mensaje}</div>
                )}

                {error && (
                    <div className="mensaje-error">{error}</div>
                )}

                <div className="empresas-resumen">
                    <div className="resumen-item">
                        <Fuel size={22} />
                        <div>
                            <span>Litros asignados</span>
                            <strong>{totalAsignado.toLocaleString("es-BO")} L</strong>
                        </div>
                    </div>

                    <div className="resumen-item">
                        <Fuel size={22} />
                        <div>
                            <span>Litros disponibles</span>
                            <strong>{totalDisponible.toLocaleString("es-BO")} L</strong>
                        </div>
                    </div>

                    <div className="resumen-item">
                        <CalendarDays size={22} />
                        <div>
                            <span>Cupos encontrados</span>
                            <strong>{cupos.length}</strong>
                        </div>
                    </div>
                </div>

                <form className="filtros-cupos" onSubmit={buscarCupos}>
                    <div className="campo-filtro">
                        <label>Vehículo</label>
                        <select
                            value={filtroVehiculo}
                            onChange={(e) => setFiltroVehiculo(e.target.value)}
                        >
                            <option value="">Todos los vehículos</option>
                            {vehiculos.map((vehiculo) => (
                                <option
                                    key={vehiculo.id_vehiculo}
                                    value={vehiculo.id_vehiculo}
                                >
                                    {vehiculo.placa}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="campo-filtro">
                        <label>Semana (selecciona una fecha)</label>
                        <input
                            type="date"
                            value={filtroFecha}
                            onChange={(e) => setFiltroFecha(e.target.value)}
                        />
                    </div>

                    <button type="submit" className="btn-principal">
                        <Search size={17} />
                        Buscar
                    </button>

                    <button
                        type="button"
                        className="btn-secundario"
                        onClick={limpiarFiltros}
                    >
                        Limpiar
                    </button>
                </form>

                <div className="tabla-contenedor">
                    <table className="tabla-empresas">
                        <thead>
                            <tr>
                                <th>Vehículo</th>
                                <th>Litros asignados</th>
                                <th>Litros disponibles</th>
                                <th>Inicio de semana</th>
                                <th>Fin de semana</th>
                                <th>Fecha de asignación</th>
                            </tr>
                        </thead>

                        <tbody>
                            {cargando ? (
                                <tr>
                                    <td colSpan="6" className="tabla-vacia">
                                        Cargando cupos...
                                    </td>
                                </tr>
                            ) : cupos.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="tabla-vacia">
                                        No se encontraron cupos registrados.
                                    </td>
                                </tr>
                            ) : (
                                cupos.map((cupo) => (
                                    <tr key={cupo.id_cupo}>
                                        <td>
                                            <div className="celda-vehiculo">
                                                <Truck size={18} />
                                                <strong>
                                                    {obtenerPlaca(cupo.id_vehiculo)}
                                                </strong>
                                            </div>
                                        </td>

                                        <td>
                                            {Number(cupo.litros_asignados).toLocaleString("es-BO")} L
                                        </td>

                                        <td>
                                            <strong>
                                                {Number(cupo.litros_disponibles).toLocaleString("es-BO")} L
                                            </strong>
                                        </td>

                                        <td>{formatearFecha(cupo.fecha_inicio)}</td>
                                        <td>{formatearFecha(cupo.fecha_fin)}</td>
                                        <td>
                                            {cupo.fecha_asignacion
                                                ? new Date(cupo.fecha_asignacion).toLocaleString("es-BO")
                                                : "-"}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {modalAbierto && (
                <div className="modal-fondo">
                    <div className="modal-empresa">
                        <div className="modal-empresa-encabezado">
                            <div>
                                <h2>Asignar cupo semanal</h2>
                                <p>
                                    Registra la cantidad de diésel disponible
                                    para un vehículo.
                                </p>
                            </div>

                            <button
                                type="button"
                                className="btn-cerrar-modal"
                                onClick={() => setModalAbierto(false)}
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={registrarCupo}>
                            <div className="formulario-empresa-grid">
                                <div className="campo-completo">
                                    <label>Vehículo *</label>
                                    <select
                                        name="id_vehiculo"
                                        value={formulario.id_vehiculo}
                                        onChange={cambiarCampo}
                                        required
                                    >
                                        <option value="">
                                            Selecciona un vehículo
                                        </option>

                                        {vehiculos
                                            .filter((vehiculo) => vehiculo.activo)
                                            .map((vehiculo) => (
                                                <option
                                                    key={vehiculo.id_vehiculo}
                                                    value={vehiculo.id_vehiculo}
                                                >
                                                    {vehiculo.placa} - {vehiculo.modelo || "Sin modelo"}
                                                </option>
                                            ))}
                                    </select>
                                </div>

                                <div className="campo-completo">
                                    <label>Litros asignados *</label>
                                    <input
                                        type="number"
                                        name="litros_asignados"
                                        min="0.01"
                                        step="0.01"
                                        placeholder="Ej. 500"
                                        value={formulario.litros_asignados}
                                        onChange={cambiarCampo}
                                        required
                                    />
                                </div>

                                <div className="campo-completo">
                                    <label>Fecha de la semana *</label>
                                    <input
                                        type="date"
                                        name="fecha_inicio"
                                        value={formulario.fecha_inicio}
                                        onChange={cambiarCampo}
                                        required
                                    />
                                    <small>
                                        El sistema calculará automáticamente
                                        el lunes y domingo de esa semana.
                                    </small>
                                </div>
                            </div>

                            <div className="acciones-modal">
                                <button
                                    type="button"
                                    className="btn-secundario"
                                    onClick={() => setModalAbierto(false)}
                                    disabled={guardando}
                                >
                                    Cancelar
                                </button>

                                <button
                                    type="submit"
                                    className="btn-principal"
                                    disabled={guardando}
                                >
                                    {guardando ? "Guardando..." : "Registrar cupo"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </AdminLayout>
    );
}

export default Cupos;
