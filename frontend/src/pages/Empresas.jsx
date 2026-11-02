
import { useEffect, useState } from "react";
import { Plus, Search, Building2, X, Pencil, Power,} from "lucide-react";
import api from "../services/api";
import AdminLayout from "../layouts/AdminLayout";
import "../estilos/empresas.css";
import "../estilos/crud-admin.css";
import "../estilos/admin-modules.css";
import "../estilos/empresas-page.css";

function Empresas() {
    const [empresas, setEmpresas] = useState([]);
    const [busqueda, setBusqueda] = useState("");
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");

    const [mostrarFormulario, setMostrarFormulario] = useState(false);
    const [guardando, setGuardando] = useState(false);
    const [mensaje, setMensaje] = useState("");
    const [tipoMensaje, setTipoMensaje] = useState("success");
    const [empresaEditando, setEmpresaEditando] = useState(null);

    const [formulario, setFormulario] = useState({
        nombre_empresa: "",
        nit: "",
        telefono: "",
    });

    const cargarEmpresas = async () => {
        try {
            setCargando(true);
            setError("");

            const respuesta = await api.get("/empresas");
            setEmpresas(respuesta.data.empresas);
        } catch (err) {
            setTipoMensaje("error");
            setError(
                err.response?.data?.error ||
                "No se pudieron cargar las empresas."
            );
        } finally {
            setCargando(false);
        }
    };

    useEffect(() => {
        cargarEmpresas();
    }, []);

    const manejarCambio = (e) => {
        setFormulario({
            ...formulario,
            [e.target.name]: e.target.value,
        });
    };

    const prepararEdicion = (empresa) => {
        setEmpresaEditando(empresa);

        setFormulario({
            nombre_empresa: empresa.nombre_empresa,
            nit: empresa.nit,
            telefono: empresa.telefono || "",
        });

        setMensaje("");
        setMostrarFormulario(true);
    };

    const cambiarEstadoEmpresa = async (empresa) => {
        const nuevoEstado = !empresa.activa;

        const accion = nuevoEstado ? "activar" : "desactivar";

        const confirmar = window.confirm(
            `¿Estás seguro de que deseas ${accion} la empresa "${empresa.nombre_empresa}"?`
        );

        if (!confirmar) {
            return;
        }

        try {
            setMensaje("");

            const respuesta = await api.patch(
                `/empresas/${empresa.id_empresa}/estado`,
                {
                    activa: nuevoEstado,
                }
            );

            setMensaje(
                respuesta.data.mensaje ||
                `Empresa ${nuevoEstado ? "activada" : "desactivada"} correctamente.`
            );

            await cargarEmpresas();

        } catch (err) {
            setTipoMensaje("error");
            setMensaje(
                err.response?.data?.error ||
                `No se pudo ${accion} la empresa.`
            );
        }
    };

    const registrarEmpresa = async (e) => {
        e.preventDefault();

        try {
            setGuardando(true);
            setMensaje("");

            let respuesta;

            if (empresaEditando) {
                respuesta = await api.patch(
                    `/empresas/${empresaEditando.id_empresa}`,
                    formulario
                );

                setMensaje(
                    respuesta.data.mensaje ||
                    "Empresa actualizada correctamente."
                );
            } else {
                respuesta = await api.post("/empresas", formulario);

                setMensaje(
                    respuesta.data.mensaje ||
                    "Empresa registrada correctamente."
                );
            }

            setFormulario({
                nombre_empresa: "",
                nit: "",
                telefono: "",
            });

            setEmpresaEditando(null);
            setMostrarFormulario(false);

            await cargarEmpresas();

        } catch (err) {
            setMensaje(
                err.response?.data?.error ||
                "No se pudo guardar la información de la empresa."
            );
        } finally {
            setGuardando(false);
        }
    };

    const empresasFiltradas = empresas.filter((empresa) =>
        empresa.nombre_empresa.toLowerCase().includes(busqueda.toLowerCase()) ||
        empresa.nit.toLowerCase().includes(busqueda.toLowerCase())
    );

    return (
        <AdminLayout>
            <div className="empresas-pagina">

                <div className="empresas-encabezado">
                    <div>
                        <h1>Empresas</h1>
                        <p>Administración de empresas de transporte.</p>
                    </div>

                    <button
                        className="btn-nueva-empresa"
                        onClick={() => {
                            setMensaje("");
                            setMostrarFormulario(true);
                        }}
                    >
                        <Plus size={18} />
                        Nueva empresa
                    </button>
                </div>

                {mensaje && (
                    <p className={`mensaje-empresa ${tipoMensaje === "error" ? "error" : ""}`} role="alert">{mensaje}</p>
                )}

                {mostrarFormulario && (
                    <div className="formulario-empresa-contenedor">
                        <div className="formulario-empresa">

                            <div className="formulario-empresa-titulo">
                                {/* <h2>Registrar nueva empresa</h2> */}
                                <h2>
                                    {empresaEditando
                                        ? "Editar empresa"
                                        : "Registrar nueva empresa"}
                                </h2>

                                <button
                                    type="button"
                                    // onClick={() => setMostrarFormulario(false)}
                                    onClick={() => {
                                        setMostrarFormulario(false);
                                        setEmpresaEditando(null);
                                        setFormulario({
                                            nombre_empresa: "",
                                            nit: "",
                                            telefono: "",
                                        });
                                    }}
                                    className="btn-cerrar-formulario"
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            <form onSubmit={registrarEmpresa}>

                                <div className="campo-empresa">
                                    <label>Nombre de la empresa *</label>
                                    <input
                                        type="text"
                                        name="nombre_empresa"
                                        value={formulario.nombre_empresa}
                                        onChange={manejarCambio}
                                        maxLength={150}
                                        placeholder="Ej. Transportes del Sur"
                                        required
                                    />
                                </div>

                                <div className="campo-empresa">
                                    <label>NIT *</label>
                                    <input
                                        type="text"
                                        name="nit"
                                        value={formulario.nit}
                                        onChange={manejarCambio}
                                        maxLength={30}
                                        placeholder="Ingrese el NIT"
                                        required
                                    />
                                </div>

                                <div className="campo-empresa">
                                    <label>Teléfono</label>
                                    <input
                                        type="text"
                                        name="telefono"
                                        value={formulario.telefono}
                                        onChange={manejarCambio}
                                        maxLength={30}
                                        placeholder="Número de contacto"
                                    />
                                </div>

                                <div className="acciones-formulario">
                                    <button
                                        type="button"
                                        className="btn-cancelar"
                                        // onClick={() => setMostrarFormulario(false)}
                                        onClick={() => {
                                            setMostrarFormulario(false);
                                            setEmpresaEditando(null);
                                            setFormulario({
                                                nombre_empresa: "",
                                                nit: "",
                                                telefono: "",
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
                                        {guardando
                                            ? "Guardando..."
                                            : empresaEditando
                                                ? "Guardar cambios"
                                                : "Registrar empresa"}
                                    </button>
                                </div>

                            </form>
                        </div>
                    </div>
                )}

                <div className="empresas-resumen">
                    <Building2 size={28} />
                    <div>
                        <span>Total de empresas</span>
                        <h2>{empresas.length}</h2>
                    </div>
                </div>

                <div className="empresas-tabla-contenedor">

                    <div className="empresas-tabla-encabezado">
                        <h2>Listado de empresas</h2>

                        <div className="buscador-empresas">
                            <Search size={18} />
                            <input
                                type="text"
                                placeholder="Buscar por nombre o NIT..."
                                value={busqueda}
                                onChange={(e) => setBusqueda(e.target.value)}
                            />
                        </div>
                    </div>

                    {cargando ? (
                        <p>Cargando empresas...</p>
                    ) : error ? (
                        <p className="mensaje-error">{error}</p>
                    ) : (
                        <table className="tabla-empresas">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Nombre de empresa</th>
                                    <th>NIT</th>
                                    <th>Teléfono</th>
                                    <th>Estado</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>

                            <tbody>
                                {empresasFiltradas.map((empresa) => (
                                    <tr key={empresa.id_empresa}>
                                        <td>{empresa.id_empresa}</td>
                                        <td>{empresa.nombre_empresa}</td>
                                        <td>{empresa.nit}</td>
                                        <td>{empresa.telefono || "—"}</td>
                                        <td>
                                            <span className={
                                                empresa.activa
                                                    ? "estado-activo"
                                                    : "estado-inactivo"
                                            }>
                                                {empresa.activa ? "Activa" : "Inactiva"}
                                            </span>
                                        </td>
                                        <td className="acciones-empresa">
                                            <button
                                                type="button"
                                                className="btn-editar-empresa"
                                                onClick={() => prepararEdicion(empresa)}
                                                title="Editar empresa"
                                            >
                                                <Pencil size={16} />
                                                Editar
                                            </button>

                                            <button
                                                type="button"
                                                className={
                                                    empresa.activa
                                                        ? "btn-desactivar-empresa"
                                                        : "btn-activar-empresa"
                                                }
                                                onClick={() => cambiarEstadoEmpresa(empresa)}
                                                title={empresa.activa ? "Desactivar empresa" : "Activar empresa"}
                                            >
                                                <Power size={16} />
                                                {empresa.activa ? "Desactivar" : "Activar"}
                                            </button>
                                        </td>
                                    </tr>
                                ))}

                                {empresasFiltradas.length === 0 && (
                                    <tr>
                                        <td colSpan="6">
                                            No se encontraron empresas.
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

export default Empresas;
