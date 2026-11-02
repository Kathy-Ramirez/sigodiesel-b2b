import { useEffect, useState } from "react";
import { Power, Plus, X } from "lucide-react";
import api from "../services/api";
import AdminLayout from "../layouts/AdminLayout";
import "../estilos/admin-resource.css";
import "../estilos/admin-modules.css";

const base = { nombre: "", apellido: "", ci: "", telefono: "", email: "", password: "", rol: "TRANSPORTISTA", id_empresa: "", id_estacion: "" };
export default function Usuarios() {
    const [users, setUsers] = useState([]), [empresas, setEmpresas] = useState([]), [estaciones, setEstaciones] = useState([]), [form, setForm] = useState(base), [open, setOpen] = useState(false), [error, setError] = useState("");
    const cargar = async () => { try { const [u, e, s] = await Promise.all([api.get("/usuarios"), api.get("/empresas"), api.get("/estaciones")]); setUsers(u.data.usuarios || []); setEmpresas(e.data.empresas || []); setEstaciones(s.data.estaciones || []); } catch (x) { setError(x.response?.data?.error || "No se pudieron cargar los usuarios."); } };
    useEffect(() => { cargar(); }, []);
    const guardar = async e => { e.preventDefault(); try { const payload = { ...form, id_empresa: form.rol === "TRANSPORTISTA" ? Number(form.id_empresa) : null, id_estacion: form.rol === "DESPACHADOR" ? Number(form.id_estacion) : null }; await api.post("/usuarios", payload); setOpen(false); setForm(base); cargar(); } catch (x) { setError(x.response?.data?.error || "No se pudo registrar el usuario."); } };
    const toggle = async u => { try { await api.patch(`/usuarios/${u.id_usuario}/estado`, { activo: !u.activo }); cargar(); } catch (x) { setError(x.response?.data?.error || "No se pudo cambiar el estado."); } };
    return <AdminLayout>
        <div className="resource-page">
            <div className="resource-heading">
                <div>
                    <h1>Usuarios</h1>
                    <p>Registra y controla el acceso de los tres roles del sistema.</p>
                </div>
                <button className="resource-primary" onClick={() => setOpen(true)}>
                    <Plus size={17} /> Nuevo usuario
                </button>
            </div>
            {error && <div className="resource-error">{error}</div>}
            <div className="resource-table">
                <table>
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Correo</th>
                            <th>Rol</th>
                            <th>Asociación</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>{users.map(u => <tr key={u.id_usuario}>
                        <td>{u.nombre} {u.apellido}</td>
                        <td>{u.email}</td><td>{u.rol}</td>
                        <td>{u.id_empresa ? empresas.find(e => e.id_empresa === u.id_empresa)?.nombre_empresa : u.id_estacion ? estaciones.find(s => s.id_estacion === u.id_estacion)?.nombre_estacion : "-"}</td>
                        <td><span className={u.activo ? "resource-active" : "resource-inactive"}>{u.activo ? "Activo" : "Inactivo"}</span></td>
                        <td>
                            <button className="resource-icon" onClick={() => toggle(u)}><Power size={16} /></button></td></tr>)}{!users.length && <tr><td colSpan="6" className="resource-empty">No hay usuarios registrados.</td></tr>}</tbody></table></div></div>{open && <div className="resource-modal"><form className="resource-dialog" onSubmit={guardar}><button type="button" className="resource-close" onClick={() => setOpen(false)}><X /></button><h2>Registrar usuario</h2>{[["nombre","Nombre"],["apellido","Apellido"],["ci","CI"],["telefono","Teléfono"],["email","Correo"],["password","Contraseña"]].map(([k,l]) => <label key={k}>{l} *<input type={k === "password" ? "password" : k === "email" ? "email" : "text"} required value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })} /></label>)}<label>Rol *<select value={form.rol} onChange={e => setForm({ ...form, rol: e.target.value })}><option>ADMINISTRADOR</option><option>TRANSPORTISTA</option><option>DESPACHADOR</option></select></label>{form.rol === "TRANSPORTISTA" && <label>Empresa *<select required value={form.id_empresa} onChange={e => setForm({ ...form, id_empresa: e.target.value })}><option value="">Seleccionar</option>{empresas.filter(x => x.activa).map(x => <option key={x.id_empresa} value={x.id_empresa}>{x.nombre_empresa}</option>)}</select></label>}{form.rol === "DESPACHADOR" && <label>Estación *<select required value={form.id_estacion} onChange={e => setForm({ ...form, id_estacion: e.target.value })}><option value="">Seleccionar</option>{estaciones.filter(x => x.activa).map(x => <option key={x.id_estacion} value={x.id_estacion}>{x.nombre_estacion}</option>)}</select></label>}<button className="resource-primary">Registrar</button></form></div>}</AdminLayout>;
}
