import { useEffect, useMemo, useState } from "react";
import { Download, Fuel, History, LogOut, RefreshCw, ShieldCheck, Truck, X } from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import "../estilos/transportista-portal.css";

const qrUrl = (token) =>
    `https://api.qrserver.com/v1/create-qr-code/?size=260x260&data=${encodeURIComponent(token)}`;

function TransportistaPortal() {
    const { usuario, cerrarSesion } = useAuth();
    const [cupos, setCupos] = useState([]);
    const [historial, setHistorial] = useState([]);
    const [tab, setTab] = useState("cupos");
    const [qr, setQr] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");

    const cargar = async () => {
        try {
            setCargando(true);
            setError("");
            const [cuposResponse, historialResponse] = await Promise.all([
                api.get("/transportistas/cupos", { params: { periodo: "actual" } }),
                api.get("/transportistas/historial"),
            ]);
            setCupos(cuposResponse.data.cupos || []);
            setHistorial(historialResponse.data.despachos || []);
        } catch (e) {
            setError(e.response?.data?.error || "No se pudo cargar tu información.");
        } finally {
            setCargando(false);
        }
    };

    useEffect(() => { cargar(); }, []);

    const verQr = async (cupo) => {
        try {
            setError("");
            const response = await api.get(`/transportistas/cupos/${cupo.id_cupo}/tiquete`);
            let tiquete = response.data.tiquete;
            if (!tiquete) {
                const creado = await api.post(`/transportistas/cupos/${cupo.id_cupo}/tiquete`);
                tiquete = creado.data.tiquete;
            }
            setQr({ ...tiquete, placa: cupo.placa });
        } catch (e) {
            setError(e.response?.data?.error || "No se pudo generar el QR.");
        }
    };

    const regenerar = async () => {
        if (!qr || !window.confirm("El QR anterior dejará de funcionar. ¿Deseas regenerarlo?")) return;
        try {
            const response = await api.post(`/transportistas/cupos/${qr.id_cupo}/tiquete/regenerar`);
            setQr({ ...response.data.nuevo_tiquete, placa: qr.placa });
        } catch (e) {
            setError(e.response?.data?.error || "No se pudo regenerar el QR.");
        }
    };

    const totales = useMemo(() => cupos.reduce((a, c) => ({
        asignados: a.asignados + Number(c.litros_asignados),
        disponibles: a.disponibles + Number(c.litros_disponibles),
    }), { asignados: 0, disponibles: 0 }), [cupos]);

    return <div className="portal-transportista">
        <header className="portal-header">
            <div><strong>SIGODIESEL</strong><span>Portal del transportista</span></div>
            <div className="portal-user"><span>{usuario?.nombre} {usuario?.apellido}</span><button onClick={cerrarSesion}><LogOut size={17} /> Salir</button></div>
        </header>
        <main className="portal-main">
            <div className="portal-heading">
                <div>
                    <h1>Mi control de cupos</h1>
                    <p>Consulta tus vehículos y el consumo de la semana vigente.</p></div>
                    {/* <button className="portal-refresh" onClick={cargar}>
                        <RefreshCw size={17} /> Actualizar</button> */}
            </div>
            {error && <div className="portal-error">{error}<button onClick={() => setError("")}><X size={16} /></button></div>}
            <div className="portal-summary"><div><Truck /><span>Vehículos con cupo</span><strong>{cupos.length}</strong></div><div><Fuel /><span>Litros asignados</span><strong>{totales.asignados.toLocaleString("es-BO")} L</strong></div><div><ShieldCheck /><span>Disponibles</span><strong>{totales.disponibles.toLocaleString("es-BO")} L</strong></div></div>
            <div className="portal-tabs"><button className={tab === "cupos" ? "active" : ""} onClick={() => setTab("cupos")}><Fuel size={17} /> Cupos vigentes</button><button className={tab === "historial" ? "active" : ""} onClick={() => setTab("historial")}><History size={17} /> Mi historial</button></div>
            {cargando ? <div className="portal-empty">Cargando información...</div> : tab === "cupos" ? <section className="portal-grid">{cupos.length === 0 ? <div className="portal-empty">No tienes cupos asignados para esta semana.</div> : cupos.map(c => <article className="cupo-card" key={c.id_cupo}><div className="cupo-card-title"><div><strong>{c.placa}</strong><span>{c.modelo || "Vehículo"}</span></div><span className="vigente">VIGENTE</span></div><div className="cupo-meter"><div style={{ width: `${Math.min(100, Number(c.litros_disponibles) / Number(c.litros_asignados) * 100)}%` }} /></div><div className="cupo-values"><span>Asignados <b>{c.litros_asignados} L</b></span><span>Consumidos <b>{c.litros_consumidos} L</b></span><span>Disponibles <b>{c.litros_disponibles} L</b></span></div><button className="portal-primary" disabled={Number(c.litros_disponibles) <= 0} onClick={() => verQr(c)}>Ver / generar QR</button></article>)}</section> : <section className="portal-history"><table><thead><tr><th>Fecha</th><th>Placa</th><th>Estación</th><th>Litros</th><th>Estado</th></tr></thead><tbody>{historial.length === 0 ? <tr><td colSpan="5" className="portal-empty">No hay despachos registrados.</td></tr> : historial.map(d => <tr key={d.id_transaccion}><td>{d.fecha_hora ? new Date(d.fecha_hora).toLocaleString("es-BO") : "-"}</td><td><strong>{d.placa}</strong></td><td>{d.estacion || d.nombre_estacion}</td><td>{d.litros_cargados} L</td><td><span className={d.estado === "REGISTRADA" ? "estado-ok" : "estado-bad"}>{d.estado}</span></td></tr>)}</tbody></table></section>}
        </main>
        {qr && <div className="portal-modal" onClick={() => setQr(null)}><div className="qr-dialog" onClick={e => e.stopPropagation()}><button className="qr-close" onClick={() => setQr(null)}><X /></button><h2>QR de {qr.placa}</h2><p>Presenta este código en la estación de servicio.</p><img src={qrUrl(qr.token_qr)} alt={`Código QR del vehículo ${qr.placa}`} /><code>{qr.token_qr}</code><div className="qr-actions"><a href={qrUrl(qr.token_qr)} download={`qr-${qr.placa}.png`} target="_blank" rel="noreferrer"><Download size={17} /> Descargar QR</a><button onClick={regenerar}><RefreshCw size={17} /> Regenerar</button></div></div></div>}
    </div>;
}

export default TransportistaPortal;
