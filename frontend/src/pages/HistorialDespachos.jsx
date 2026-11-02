
import { useEffect, useState } from "react";
import { Search, Download, X, Fuel, CalendarDays, Ban, Eye,} from "lucide-react";

import AdminLayout from "../layouts/AdminLayout";
import api from "../services/api";
import "../estilos/admin-modules.css";

function formatearFecha(fecha) {
    if (!fecha) return "-";

    return new Date(fecha).toLocaleString("es-BO", {
        dateStyle: "short",
        timeStyle: "short",
    });
}

function HistorialDespachos() {
    const [despachos, setDespachos] = useState([]);
    const [estaciones, setEstaciones] = useState([]);

    const [cargando, setCargando] = useState(true);
    const [exportando, setExportando] = useState(false);
    const [error, setError] = useState("");
    const [mensaje, setMensaje] = useState("");

    const [filtros, setFiltros] = useState({
        fecha_desde: "",
        fecha_hasta: "",
        placa: "",
        id_estacion: "",
        estado: "",
    });

    const [despachoSeleccionado, setDespachoSeleccionado] = useState(null);
    const [despachoAnular, setDespachoAnular] = useState(null);
    const [motivoAnulacion, setMotivoAnulacion] = useState("");
    const [anulando, setAnulando] = useState(false);

    const cargarHistorial = async (parametros = {}) => {
        try {
            setCargando(true);
            setError("");

            const respuesta = await api.get("/despachos/historial", {
                params: parametros,
            });

            setDespachos(respuesta.data.historial || []);
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudo cargar el historial de despachos."
            );
        } finally {
            setCargando(false);
        }
    };

    const cargarEstaciones = async () => {
        try {
            const respuesta = await api.get("/estaciones");
            setEstaciones(respuesta.data.estaciones || []);
        } catch (err) {
            console.error("No se pudieron cargar las estaciones:", err);
        }
    };

    useEffect(() => {
        cargarHistorial();
        cargarEstaciones();
    }, []);

    const cambiarFiltro = (e) => {
        const { name, value } = e.target;

        setFiltros((actual) => ({
            ...actual,
            [name]: value,
        }));
    };

    const buscar = async (e) => {
        e.preventDefault();

        if (
            filtros.fecha_desde &&
            filtros.fecha_hasta &&
            filtros.fecha_desde > filtros.fecha_hasta
        ) {
            setError("La fecha inicial no puede ser posterior a la fecha final.");
            return;
        }

        const parametros = {};

        Object.entries(filtros).forEach(([clave, valor]) => {
            if (valor !== "") {
                parametros[clave] = valor;
            }
        });

        setMensaje("");
        await cargarHistorial(parametros);
    };

    const limpiarFiltros = async () => {
        const filtrosVacios = {
            fecha_desde: "",
            fecha_hasta: "",
            placa: "",
            id_estacion: "",
            estado: "",
        };

        setFiltros(filtrosVacios);
        setMensaje("");
        await cargarHistorial();
    };

    const exportarCSV = async () => {
        try {
            setExportando(true);
            setError("");

            const parametros = {};

            Object.entries(filtros).forEach(([clave, valor]) => {
                if (valor !== "") {
                    parametros[clave] = valor;
                }
            });

            const respuesta = await api.get(
                "/despachos/historial/exportar-csv",
                {
                    params: parametros,
                    responseType: "blob",
                }
            );

            const archivo = new Blob(
                ["\uFEFF", respuesta.data],
                { type: "text/csv;charset=utf-8;" }
            );

            const url = window.URL.createObjectURL(archivo);
            const enlace = document.createElement("a");

            enlace.href = url;
            enlace.download = "historial_despachos.csv";

            document.body.appendChild(enlace);
            enlace.click();
            enlace.remove();

            window.URL.revokeObjectURL(url);
        } catch (err) {
            setError(
                "No se pudo exportar el historial. Verifica tus permisos."
            );
        } finally {
            setExportando(false);
        }
    };

    const confirmarAnulacion = async (e) => {
        e.preventDefault();

        if (!motivoAnulacion.trim()) {
            setError("Debes ingresar el motivo de la anulación.");
            return;
        }

        try {
            setAnulando(true);
            setError("");
            setMensaje("");

            const respuesta = await api.post(
                `/despachos/${despachoAnular.id_transaccion}/anular`,
                {
                    motivo_anulacion: motivoAnulacion.trim(),
                }
            );

            setMensaje(respuesta.data.mensaje);
            setDespachoAnular(null);
            setMotivoAnulacion("");

            const parametros = {};

            Object.entries(filtros).forEach(([clave, valor]) => {
                if (valor !== "") {
                    parametros[clave] = valor;
                }
            });

            await cargarHistorial(parametros);
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudo anular el despacho."
            );
        } finally {
            setAnulando(false);
        }
    };

    const totalLitros = despachos.reduce(
        (total, despacho) =>
            total + Number(despacho.litros_cargados),
        0
    );

    const totalRegistrados = despachos.filter(
        (despacho) => despacho.estado === "REGISTRADA"
    ).length;

    const totalAnulados = despachos.filter(
        (despacho) => despacho.estado === "ANULADA"
    ).length;

    return (
        <AdminLayout>
            <div className="pagina-empresas">
                <div className="encabezado-modulo">
                    <div>
                        <h1>Historial de despachos</h1>
                        <p>
                            Consulta y administra los despachos de diésel
                            registrados en el sistema.
                        </p>
                    </div>

                    <button
                        className="btn-principal"
                        onClick={exportarCSV}
                        disabled={exportando}
                    >
                        <Download size={18} />
                        {exportando ? "Exportando..." : "Exportar CSV"}
                    </button>
                </div>

                {mensaje && (
                    <div className="mensaje-exito">
                        {mensaje}
                    </div>
                )}

                {error && (
                    <div className="mensaje-error">
                        {error}
                    </div>
                )}

                <div className="empresas-resumen">
                    <div className="resumen-item">
                        <Fuel size={22} />
                        <div>
                            <span>Litros despachados</span>
                            <strong>
                                {totalLitros.toLocaleString("es-BO")} L
                            </strong>
                        </div>
                    </div>

                    <div className="resumen-item">
                        <CalendarDays size={22} />
                        <div>
                            <span>Despachos registrados</span>
                            <strong>{totalRegistrados}</strong>
                        </div>
                    </div>

                    <div className="resumen-item">
                        <Ban size={22} />
                        <div>
                            <span>Despachos anulados</span>
                            <strong>{totalAnulados}</strong>
                        </div>
                    </div>
                </div>

                <form className="filtros-cupos" onSubmit={buscar}>
                    <div className="campo-filtro">
                        <label>Desde</label>
                        <input
                            type="date"
                            name="fecha_desde"
                            value={filtros.fecha_desde}
                            onChange={cambiarFiltro}
                        />
                    </div>

                    <div className="campo-filtro">
                        <label>Hasta</label>
                        <input
                            type="date"
                            name="fecha_hasta"
                            value={filtros.fecha_hasta}
                            onChange={cambiarFiltro}
                        />
                    </div>

                    <div className="campo-filtro">
                        <label>Placa</label>
                        <input
                            type="text"
                            name="placa"
                            placeholder="Buscar placa..."
                            value={filtros.placa}
                            onChange={cambiarFiltro}
                        />
                    </div>

                    <div className="campo-filtro">
                        <label>Estación</label>
                        <select
                            name="id_estacion"
                            value={filtros.id_estacion}
                            onChange={cambiarFiltro}
                        >
                            <option value="">Todas las estaciones</option>

                            {estaciones.map((estacion) => (
                                <option
                                    key={estacion.id_estacion}
                                    value={estacion.id_estacion}
                                >
                                    {estacion.nombre_estacion}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="campo-filtro">
                        <label>Estado</label>
                        <select
                            name="estado"
                            value={filtros.estado}
                            onChange={cambiarFiltro}
                        >
                            <option value="">Todos</option>
                            <option value="REGISTRADA">Registrada</option>
                            <option value="ANULADA">Anulada</option>
                        </select>
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
                                <th>N.º</th>
                                <th>Fecha y hora</th>
                                <th>Vehículo</th>
                                <th>Empresa</th>
                                <th>Estación</th>
                                <th>Isla</th>
                                <th>Litros</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>

                        <tbody>
                            {cargando ? (
                                <tr>
                                    <td colSpan="9" className="tabla-vacia">
                                        Cargando historial...
                                    </td>
                                </tr>
                            ) : despachos.length === 0 ? (
                                <tr>
                                    <td colSpan="9" className="tabla-vacia">
                                        No se encontraron despachos.
                                    </td>
                                </tr>
                            ) : (
                                despachos.map((despacho) => (
                                    <tr key={despacho.id_transaccion}>
                                        <td>{despacho.id_transaccion}</td>
                                        <td>{formatearFecha(despacho.fecha_hora)}</td>
                                        <td>
                                            <strong>{despacho.placa}</strong>
                                        </td>
                                        <td>{despacho.nombre_empresa}</td>
                                        <td>{despacho.nombre_estacion}</td>
                                        <td>{despacho.nro_isla}</td>
                                        <td>
                                            {Number(
                                                despacho.litros_cargados
                                            ).toLocaleString("es-BO")} L
                                        </td>
                                        <td>
                                            <span
                                                className={`estado-despacho ${
                                                    despacho.estado === "REGISTRADA"
                                                        ? "estado-registrada"
                                                        : "estado-anulada"
                                                }`}
                                            >
                                                {despacho.estado}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="acciones-tabla">
                                                <button
                                                    type="button"
                                                    className="btn-accion btn-ver"
                                                    title="Ver detalles"
                                                    onClick={() =>
                                                        setDespachoSeleccionado(despacho)
                                                    }
                                                >
                                                    <Eye size={17} />
                                                </button>

                                                {despacho.estado === "REGISTRADA" && (
                                                    <button
                                                        type="button"
                                                        className="btn-accion btn-anular"
                                                        title="Anular despacho"
                                                        onClick={() => {
                                                            setError("");
                                                            setMotivoAnulacion("");
                                                            setDespachoAnular(despacho);
                                                        }}
                                                    >
                                                        <Ban size={17} />
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                <p className="texto-secundario">
                    Se encontraron {despachos.length} despachos.
                </p>
            </div>

            {despachoSeleccionado && (
                <div
                    className="modal-fondo"
                    onClick={() => setDespachoSeleccionado(null)}
                >
                    <div
                        className="modal-empresa modal-despacho"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modal-empresa-encabezado">
                            <div>
                                <h2>Detalle del despacho</h2>
                                <p>
                                    Transacción #{despachoSeleccionado.id_transaccion}
                                </p>
                            </div>

                            <button
                                className="btn-cerrar-modal"
                                onClick={() => setDespachoSeleccionado(null)}
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <div className="detalle-despacho">
                            <p><strong>Placa:</strong> {despachoSeleccionado.placa}</p>
                            <p><strong>Modelo:</strong> {despachoSeleccionado.modelo || "-"}</p>
                            <p><strong>Empresa:</strong> {despachoSeleccionado.nombre_empresa}</p>
                            <p><strong>Estación:</strong> {despachoSeleccionado.nombre_estacion}</p>
                            <p><strong>Número de isla:</strong> {despachoSeleccionado.nro_isla}</p>
                            <p><strong>Litros cargados:</strong> {despachoSeleccionado.litros_cargados} L</p>
                            <p><strong>Fecha:</strong> {formatearFecha(despachoSeleccionado.fecha_hora)}</p>
                            <p><strong>Estado:</strong> {despachoSeleccionado.estado}</p>
                            <p><strong>ID de operación:</strong> {despachoSeleccionado.id_operacion}</p>

                            {despachoSeleccionado.estado === "ANULADA" && (
                                <>
                                    <p>
                                        <strong>Fecha de anulación:</strong>{" "}
                                        {formatearFecha(despachoSeleccionado.fecha_anulacion)}
                                    </p>
                                    <p>
                                        <strong>Motivo:</strong>{" "}
                                        {despachoSeleccionado.motivo_anulacion || "-"}
                                    </p>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {despachoAnular && (
                <div className="modal-fondo">
                    <div className="modal-empresa">
                        <div className="modal-empresa-encabezado">
                            <div>
                                <h2>Anular despacho</h2>
                                <p>
                                    Transacción #{despachoAnular.id_transaccion}
                                </p>
                            </div>

                            <button
                                className="btn-cerrar-modal"
                                onClick={() => setDespachoAnular(null)}
                                disabled={anulando}
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <div className="alerta-anulacion">
                            <strong>Atención:</strong> esta acción marcará
                            el despacho como anulado y restaurará los litros
                            correspondientes al cupo.
                        </div>

                        <form onSubmit={confirmarAnulacion}>
                            <div className="campo-completo">
                                <label>Motivo de anulación *</label>
                                <textarea
                                    rows="4"
                                    maxLength="500"
                                    value={motivoAnulacion}
                                    onChange={(e) =>
                                        setMotivoAnulacion(e.target.value)
                                    }
                                    placeholder="Describe el motivo de la anulación..."
                                    required
                                />
                            </div>

                            <div className="acciones-modal">
                                <button
                                    type="button"
                                    className="btn-secundario"
                                    onClick={() => setDespachoAnular(null)}
                                    disabled={anulando}
                                >
                                    Cancelar
                                </button>

                                <button
                                    type="submit"
                                    className="btn-peligro"
                                    disabled={anulando || !motivoAnulacion.trim()}
                                >
                                    {anulando ? "Anulando..." : "Confirmar anulación"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </AdminLayout>
    );
}

export default HistorialDespachos;
