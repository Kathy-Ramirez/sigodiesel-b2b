import { useEffect, useState } from "react";
import { Activity, Building2, Droplets, Fuel, Truck, Users } from "lucide-react";
import AdminLayout from "../layouts/AdminLayout";
import api from "../services/api";
import "../estilos/dashboard.css";

const inicioSemana = () => {
    const fecha = new Date();
    const diaSemana = fecha.getDay() || 7;
    fecha.setDate(fecha.getDate() - diaSemana + 1);
    fecha.setHours(0, 0, 0, 0);
    return fecha;
};

const claveFechaLocal = (fecha) => {
    const anio = fecha.getFullYear();
    const mes = String(fecha.getMonth() + 1).padStart(2, "0");
    const dia = String(fecha.getDate()).padStart(2, "0");
    return `${anio}-${mes}-${dia}`;
};

function Dashboard() {
    const [datos, setDatos] = useState({ empresas: 0, vehiculos: 0, transportistas: 0, despachos: 0, litros: 0, disponibles: 0 });
    const [serieSemana, setSerieSemana] = useState([]);
    const [ultimosDespachos, setUltimosDespachos] = useState([]);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        Promise.all([
            api.get("/empresas"),
            api.get("/vehiculos"),
            api.get("/usuarios"),
            api.get("/cupos"),
            api.get("/despachos/historial"),
        ]).then(([empresasResponse, vehiculosResponse, usuariosResponse, cuposResponse, despachosResponse]) => {
            const semana = inicioSemana();
            const cupos = cuposResponse.data || [];
            const cuposActuales = cupos.filter((cupo) => new Date(`${cupo.fecha_inicio}T00:00:00`) >= semana);
            const historial = despachosResponse.data.historial || [];
            const registrados = historial.filter((despacho) => despacho.estado === "REGISTRADA");

            setDatos({
                empresas: (empresasResponse.data.empresas || []).filter((empresa) => empresa.activa).length,
                vehiculos: (vehiculosResponse.data.vehiculos || []).filter((vehiculo) => vehiculo.activo).length,
                transportistas: (usuariosResponse.data.usuarios || []).filter((usuario) => usuario.rol === "TRANSPORTISTA" && usuario.activo).length,
                despachos: historial.filter((despacho) => new Date(despacho.fecha_hora) >= semana && despacho.estado === "REGISTRADA").length,
                litros: historial.filter((despacho) => despacho.estado === "REGISTRADA" && new Date(despacho.fecha_hora) >= semana).reduce((total, despacho) => total + Number(despacho.litros_cargados || 0), 0),
                disponibles: cuposActuales.reduce((total, cupo) => total + Number(cupo.litros_disponibles || 0), 0),
            });

            const actividad = Array.from({ length: 7 }, (_, indice) => {
                const fecha = new Date(semana);
                fecha.setDate(semana.getDate() + indice);
                const fechaClave = claveFechaLocal(fecha);
                const litros = registrados
                    .filter((despacho) => {
                        const fechaDespacho = new Date(despacho.fecha_hora);
                        return claveFechaLocal(fechaDespacho) === fechaClave;
                    })
                    .reduce((total, despacho) => total + Number(despacho.litros_cargados || 0), 0);

                return {
                    fecha: fechaClave,
                    etiqueta: fecha.toLocaleDateString("es-BO", { weekday: "short" }).replace(".", ""),
                    titulo: fecha.toLocaleDateString("es-BO", { dateStyle: "full" }),
                    litros,
                };
            });

            setSerieSemana(actividad);
            setUltimosDespachos([...historial]
                .sort((a, b) => new Date(b.fecha_hora) - new Date(a.fecha_hora))
                .slice(0, 5));
        }).catch(() => {
            setError("No se pudo cargar el resumen operativo. Intenta actualizar la página.");
        }).finally(() => setCargando(false));
    }, []);

    const cards = [
        [Building2, "Empresas activas", datos.empresas, "blue"],
        [Truck, "Vehículos activos", datos.vehiculos, "cyan"],
        [Users, "Transportistas", datos.transportistas, "violet"],
        [Activity, "Despachos esta semana", datos.despachos, "amber"],
        [Fuel, "Litros despachados", `${datos.litros.toLocaleString("es-BO")} L`, "green"],
        [Droplets, "Saldo disponible", `${datos.disponibles.toLocaleString("es-BO")} L`, "teal"],
    ];
    const maxLitrosSemana = Math.max(...serieSemana.map((dia) => dia.litros), 1);

    return (
        <AdminLayout>
            <div className="dashboard-page">
                <div className="dashboard-header">
                    <div>
                        <p className="dashboard-kicker">CENTRO DE CONTROL</p>
                        <h1>Panel administrativo</h1>
                        <p>Resumen operativo de SIGODIESEL B2B.</p>
                    </div>
                    <div className="dashboard-live"><span /> Datos del sistema</div>
                </div>

                {error && <div className="dashboard-error" role="alert">{error}</div>}

                <section className="dashboard-stats" aria-label="Indicadores operativos">
                    {cards.map(([Icon, label, value, color]) => (
                        <article className={`dashboard-stat ${color}`} key={label}>
                            <div className="dashboard-stat-icon"><Icon size={20} aria-hidden="true" /></div>
                            <div className="dashboard-stat-copy">
                                <span>{label}</span>
                                <strong>{cargando ? "—" : value}</strong>
                            </div>
                        </article>
                    ))}
                </section>

                <div className="dashboard-grid">
                    <section className="dashboard-panel dashboard-chart-panel">
                        <div className="dashboard-panel-heading">
                            <div>
                                <p className="dashboard-kicker">ACTIVIDAD SEMANAL</p>
                                <h2>Litros despachados por día</h2>
                            </div>
                            <span className="dashboard-panel-unit">LITROS</span>
                        </div>
                        {cargando ? (
                            <div className="dashboard-chart-loading" role="status">Cargando actividad...</div>
                        ) : (
                            <div className="dashboard-chart" role="img" aria-label="Litros despachados cada día de la semana">
                                {serieSemana.map((dia) => (
                                    <div className="dashboard-chart-column" key={dia.fecha} title={`${dia.titulo}: ${dia.litros.toLocaleString("es-BO")} L`}>
                                        <strong>{dia.litros ? dia.litros.toLocaleString("es-BO") : ""}</strong>
                                        <div className="dashboard-chart-track">
                                            <span style={{ height: `${dia.litros ? Math.max(5, (dia.litros / maxLitrosSemana) * 100) : 0}%` }} />
                                        </div>
                                        <small>{dia.etiqueta}</small>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>

                    <section className="dashboard-panel dashboard-recent-panel">
                        <div className="dashboard-panel-heading">
                            <div>
                                <p className="dashboard-kicker">TRAZABILIDAD</p>
                                <h2>Despachos recientes</h2>
                            </div>
                        </div>
                        {cargando ? (
                            <p className="dashboard-empty">Cargando despachos...</p>
                        ) : ultimosDespachos.length === 0 ? (
                            <p className="dashboard-empty">No hay despachos para mostrar.</p>
                        ) : (
                            <div className="dashboard-recent-list">
                                {ultimosDespachos.map((despacho) => (
                                    <article className="dashboard-recent-row" key={despacho.id_transaccion}>
                                        <span className={`dashboard-recent-status ${despacho.estado === "REGISTRADA" ? "is-registered" : "is-cancelled"}`} aria-hidden="true" />
                                        <div className="dashboard-recent-main">
                                            <strong>{despacho.placa || "Vehículo"}</strong>
                                            <span>{despacho.nombre_estacion || despacho.estacion || "Estación"}</span>
                                        </div>
                                        <div className="dashboard-recent-meta">
                                            <strong>{Number(despacho.litros_cargados || 0).toLocaleString("es-BO")} L</strong>
                                            <span>{despacho.fecha_hora ? new Date(despacho.fecha_hora).toLocaleDateString("es-BO") : "—"}</span>
                                        </div>
                                    </article>
                                ))}
                            </div>
                        )}
                    </section>
                </div>
            </div>
        </AdminLayout>
    );
}

export default Dashboard;
