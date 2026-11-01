import { useEffect, useState } from "react";
import { Search, Truck, Plus, X, Pencil, Power, } from "lucide-react";
import api from "../services/api";
import AdminLayout from "../layouts/AdminLayout";

function Vehiculos() {
    const [vehiculos, setVehiculos] = useState([]);
    const [empresas, setEmpresas] = useState([]);
    const [busqueda, setBusqueda] = useState("");
    const [mostrarFormulario, setMostrarFormulario] = useState(false);
    const [guardando, setGuardando] = useState(false);
    const [mensaje, setMensaje] = useState("");

    const [formulario, setFormulario] = useState({
        placa: "",
        id_empresa: "",
        modelo: "",
        capacidad_tanque: "",
    });

    const [vehiculoEditando, setVehiculoEditando] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");

    const cargarDatos = async () => {
        try {
            setCargando(true);
            setError("");

            const [respuestaVehiculos, respuestaEmpresas] =
                await Promise.all([
                    api.get("/vehiculos"),
                    api.get("/empresas"),
                ]);

            setVehiculos(respuestaVehiculos.data.vehiculos);
            setEmpresas(respuestaEmpresas.data.empresas);

        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudieron cargar los vehículos."
            );
        } finally {
            setCargando(false);
        }
    };

    const manejarCambio = (e) => {
        setFormulario({
            ...formulario,
            [e.target.name]: e.target.value,
        });
    };

    const registrarVehiculo = async (e) => {
        e.preventDefault();

        try {
            setGuardando(true);
            setMensaje("");

            const datosVehiculo = {
                placa: formulario.placa.trim().toUpperCase(),
                id_empresa: Number(formulario.id_empresa),
                modelo: formulario.modelo.trim(),
                capacidad_tanque: Number(formulario.capacidad_tanque),
            };

            let respuesta;
            if (vehiculoEditando) {
                respuesta = await api.patch(
                    `/vehiculos/${vehiculoEditando.id_vehiculo}`,
                    datosVehiculo
                );
            } else {
                respuesta = await api.post(
                    "/vehiculos",
                    datosVehiculo
                );
            }

            setMensaje(
                respuesta.data.mensaje ||
                ( vehiculoEditando ? "Vehículo actualizado correctamente." : "Vehículo registrado correctamente.")
            );

            setFormulario({
                placa: "",
                id_empresa: "",
                modelo: "",
                capacidad_tanque: "",
            });
            setVehiculoEditando(null);
            setMostrarFormulario(false);

            await cargarDatos();

        } catch (err) {
            setMensaje(
                err.response?.data?.error ||
                "No se pudo registrar el vehículo."
            );
        } finally {
            setGuardando(false);
        }
    };

    const prepararEdicion = (vehiculo) => {
        setVehiculoEditando(vehiculo);

        setFormulario({
            placa: vehiculo.placa,
            id_empresa: String(vehiculo.id_empresa),
            modelo: vehiculo.modelo || "",
            capacidad_tanque: String(vehiculo.capacidad_tanque),
        });

        setMensaje("");
        setMostrarFormulario(true);
    };

    const cambiarEstadoVehiculo = async (vehiculo) => {
        const nuevoEstado = !vehiculo.activo;

        const accion = nuevoEstado ? "activar" : "desactivar";

        const confirmar = window.confirm(
            `¿Estás seguro de que deseas ${accion} el vehículo ${vehiculo.placa}?`
        );

        if (!confirmar) return;

        try {
            setMensaje("");

            const respuesta = await api.patch(
                `/vehiculos/${vehiculo.id_vehiculo}/estado`,
                {
                    activo: nuevoEstado,
                }
            );

            setMensaje(
                respuesta.data.mensaje ||
                `Vehículo ${nuevoEstado ? "activado" : "desactivado"} correctamente.`
            );

            await cargarDatos();

        } catch (err) {
            setMensaje(
                err.response?.data?.error ||
                `No se pudo ${accion} el vehículo.`
            );
        }
    };

    useEffect(() => {
        cargarDatos();
    }, []);

    const vehiculosFiltrados = vehiculos.filter((vehiculo) => {
        const empresa = empresas.find(
            (item) => item.id_empresa === vehiculo.id_empresa
        );

        const nombreEmpresa = empresa?.nombre_empresa || "";

        return (
            vehiculo.placa.toLowerCase().includes(busqueda.toLowerCase()) ||
            nombreEmpresa.toLowerCase().includes(busqueda.toLowerCase()) ||
            (vehiculo.modelo || "").toLowerCase().includes(busqueda.toLowerCase())
        );
    });

    return (
        <AdminLayout>
            <div className="vehiculos-pagina">

                <div className="vehiculos-encabezado">
                    <div>
                        <h1>Vehículos</h1>
                        <p>
                            Administración de vehículos de las empresas
                            de transporte.
                        </p>
                    </div>

                    <button
                        className="btn-nueva-empresa"
                        onClick={() => {
                            setMensaje("");
                            setVehiculoEditando(null);
                            setFormulario({
                                placa: "",
                                id_empresa: "",
                                modelo: "",
                                capacidad_tanque: "",
                            });
                            setMostrarFormulario(true);
                        }}
                    >
                        <Plus size={18} />
                        Nuevo vehículo
                    </button>
                </div>

{/* FORMULARIO  */}
                {mensaje && (
                    <p className="mensaje-empresa">{mensaje}</p>
                )}

                {mostrarFormulario && (
                    <div className="formulario-empresa-contenedor">
                        <div className="formulario-empresa">

                            <div className="formulario-empresa-titulo">
                                {/* <h2>Registrar nuevo vehículo</h2> */}
                                <h2>
                                    {vehiculoEditando
                                        ? "Editar vehículo"
                                        : "Registrar nuevo vehículo"}
                                </h2>

                                <button
                                    type="button"
                                    // onClick={() => setMostrarFormulario(false)}
                                    onClick={() => {
                                        setMostrarFormulario(false);
                                        setVehiculoEditando(null);
                                        setFormulario({
                                            placa: "",
                                            id_empresa: "",
                                            modelo: "",
                                            capacidad_tanque: "",
                                        });
                                    }}
                                    className="btn-cerrar-formulario"
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            <form onSubmit={registrarVehiculo}>

                                <div className="campo-empresa">
                                    <label>Placa *</label>
                                    <input
                                        type="text"
                                        name="placa"
                                        value={formulario.placa}
                                        onChange={manejarCambio}
                                        maxLength={20}
                                        placeholder="Ej. 1234ABC"
                                        required
                                    />
                                </div>

                                <div className="campo-empresa">
                                    <label>Empresa *</label>
                                    <select
                                        name="id_empresa"
                                        value={formulario.id_empresa}
                                        onChange={manejarCambio}
                                        required
                                    >
                                        <option value="">Seleccione una empresa</option>

                                        {empresas
                                            .filter((empresa) => empresa.activa)
                                            .map((empresa) => (
                                                <option
                                                    key={empresa.id_empresa}
                                                    value={empresa.id_empresa}
                                                >
                                                    {empresa.nombre_empresa}
                                                </option>
                                            ))}
                                    </select>
                                </div>

                                <div className="campo-empresa">
                                    <label>Modelo</label>
                                    <input
                                        type="text"
                                        name="modelo"
                                        value={formulario.modelo}
                                        onChange={manejarCambio}
                                        placeholder="Ej. Volvo FH"
                                    />
                                </div>

                                <div className="campo-empresa">
                                    <label>Capacidad del tanque (litros) *</label>
                                    <input
                                        type="number"
                                        name="capacidad_tanque"
                                        value={formulario.capacidad_tanque}
                                        onChange={manejarCambio}
                                        min="0.01"
                                        step="0.01"
                                        placeholder="Ej. 500"
                                        required
                                    />
                                </div>

                                <div className="acciones-formulario">
                                    <button
                                        type="button"
                                        className="btn-cancelar"
                                        // onClick={() => setMostrarFormulario(false)}
                                        onClick={() => {
                                            setMostrarFormulario(false);
                                            setVehiculoEditando(null);
                                            setFormulario({
                                                placa: "",
                                                id_empresa: "",
                                                modelo: "",
                                                capacidad_tanque: "",
                                            });
                                        }}
                                        disabled={guardando}
                                    >
                                        Cancelar
                                    </button>

                                    <button
                                        type="submit"
                                        className="btn-guardar"
                                        disabled={guardando}
                                    >
                                        {/* {guardando ? "Guardando..." : "Registrar vehículo"} */}
                                        {guardando
                                            ? "Guardando..."
                                            : vehiculoEditando
                                                ? "Guardar cambios"
                                                : "Registrar vehículo"}
                                    </button>
                                </div>

                            </form>
                        </div>
                    </div>
                )}

                <div className="empresas-resumen">
                    <Truck size={28} />
                    <div>
                        <span>Total de vehículos</span>
                        <h2>{vehiculos.length}</h2>
                    </div>
                </div>

                <div className="empresas-tabla-contenedor">

                    <div className="empresas-tabla-encabezado">
                        <h2>Listado de vehículos</h2>

                        <div className="buscador-empresas">
                            <Search size={18} />

                            <input
                                type="text"
                                placeholder="Buscar por placa, modelo o empresa..."
                                value={busqueda}
                                onChange={(e) => setBusqueda(e.target.value)}
                            />
                        </div>
                    </div>

                    {cargando ? (
                        <p>Cargando vehículos...</p>
                    ) : error ? (
                        <p className="mensaje-error">{error}</p>
                    ) : (
                        <table className="tabla-empresas">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Placa</th>
                                    <th>Empresa</th>
                                    <th>Modelo</th>
                                    <th>Capacidad del tanque</th>
                                    <th>Estado</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>

                            <tbody>
                                {vehiculosFiltrados.map((vehiculo) => {
                                    const empresa = empresas.find(
                                        (item) =>
                                            item.id_empresa === vehiculo.id_empresa
                                    );

                                    return (
                                        <tr key={vehiculo.id_vehiculo}>
                                            <td>{vehiculo.id_vehiculo}</td>
                                            <td>{vehiculo.placa}</td>
                                            <td>
                                                {empresa?.nombre_empresa || "No encontrada"}
                                            </td>
                                            <td>{vehiculo.modelo || "—"}</td>
                                            <td>
                                                {vehiculo.capacidad_tanque} litros
                                            </td>
                                            <td>
                                                <span className={
                                                    vehiculo.activo
                                                        ? "estado-activo"
                                                        : "estado-inactivo"
                                                }>
                                                    {vehiculo.activo ? "Activo" : "Inactivo"}
                                                </span>
                                            </td>

                                            <td className="acciones-empresa">
                                                <button
                                                    type="button"
                                                    className="btn-editar-empresa"
                                                    onClick={() => prepararEdicion(vehiculo)}
                                                    title="Editar vehículo"
                                                >
                                                    <Pencil size={16} />
                                                    Editar
                                                </button>

                                                <button
                                                    type="button"
                                                    className={
                                                        vehiculo.activo
                                                            ? "btn-desactivar-empresa"
                                                            : "btn-activar-empresa"
                                                    }
                                                    onClick={() => cambiarEstadoVehiculo(vehiculo)}
                                                    title={vehiculo.activo ? "Desactivar vehículo" : "Activar vehículo"}
                                                >
                                                    <Power size={16} />
                                                    {vehiculo.activo ? "Desactivar" : "Activar"}
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })}

                                {vehiculosFiltrados.length === 0 && (
                                    <tr>
                                        <td colSpan="7">
                                            No se encontraron vehículos.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    )}

                </div>
            </div>
        </AdminLayout>
    );
}

export default Vehiculos;