import { useState } from "react";
import {
    Activity,
    Building2,
    ClipboardList,
    Fuel,
    LayoutDashboard,
    LogOut,
    Menu,
    ShieldCheck,
    Truck,
    UserCog,
    Users,
    X,
} from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../estilos/admin-theme.css";
import "../estilos/admin-modules.css";

function AdminLayout({ children }) {
    const { usuario, cerrarSesion } = useAuth();
    const [sidebarAbierto, setSidebarAbierto] = useState(false);
    const { pathname } = useLocation();

    const opcionesMenu = [
        { nombre: "Inicio", ruta: "/admin", icono: LayoutDashboard },
        { nombre: "Empresas", ruta: "/admin/empresas", icono: Building2 },
        { nombre: "Vehículos", ruta: "/admin/vehiculos", icono: Truck },
        { nombre: "Transportistas", ruta: "/admin/transportistas", icono: Users },
        { nombre: "Estaciones", ruta: "/admin/estaciones", icono: Fuel },
        { nombre: "Historial de despachos", ruta: "/admin/historial-despachos", icono: ClipboardList },
        { nombre: "Usuarios", ruta: "/admin/usuarios", icono: UserCog },
        { nombre: "Cupos semanales", ruta: "/admin/cupos", icono: Activity },
    ];

    const iniciales = [usuario?.nombre, usuario?.apellido]
        .filter(Boolean)
        .map((parte) => parte[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();
    const seccionActual = opcionesMenu.find((opcion) => opcion.ruta === pathname)?.nombre || "Administración";

    return (
        <div className="admin-layout">
            <button
                type="button"
                className={`sidebar-backdrop${sidebarAbierto ? " is-visible" : ""}`}
                onClick={() => setSidebarAbierto(false)}
                aria-label="Cerrar menú de navegación"
                tabIndex={sidebarAbierto ? 0 : -1}
            />

            <aside id="admin-sidebar" className={`sidebar${sidebarAbierto ? " sidebar-open" : ""}`}>
                <div className="sidebar-logo">
                    <div className="sidebar-brand-icon" aria-hidden="true">
                        <Fuel size={21} />
                    </div>
                    <div className="sidebar-brand-copy">
                        <h2>SIGODIESEL</h2>
                        <span>B2B · OPERACIONES</span>
                    </div>
                    <button
                        type="button"
                        className="sidebar-close"
                        onClick={() => setSidebarAbierto(false)}
                        aria-label="Cerrar menú"
                    >
                        <X size={19} />
                    </button>
                </div>

                <nav className="sidebar-menu" aria-label="Navegación principal">
                    <p className="menu-titulo">MÓDULOS</p>
                    {opcionesMenu.map((opcion) => {
                        const Icono = opcion.icono;

                        return (
                            <NavLink
                                to={opcion.ruta}
                                key={opcion.nombre}
                                end={opcion.ruta === "/admin"}
                                onClick={() => setSidebarAbierto(false)}
                                className={({ isActive }) =>
                                    isActive ? "menu-item menu-item-activo" : "menu-item"
                                }
                            >
                                <Icono size={19} aria-hidden="true" />
                                <span>{opcion.nombre}</span>
                            </NavLink>
                        );
                    })}
                </nav>

                <div className="sidebar-footer">
                    <div className="usuario-info">
                        <span className="usuario-avatar" aria-hidden="true">{iniciales || "AD"}</span>
                        <div className="usuario-info-copy">
                            <strong>{usuario?.nombre} {usuario?.apellido}</strong>
                            <span>Administrador</span>
                        </div>
                    </div>
                    <button className="btn-cerrar-sesion" onClick={cerrarSesion}>
                        <LogOut size={17} aria-hidden="true" />
                        <span>Cerrar sesión</span>
                    </button>
                </div>
            </aside>

            <main className="admin-contenido">
                <header className="admin-topbar">
                    <div className="admin-topbar-start">
                        <button
                            type="button"
                            className="sidebar-toggle"
                            onClick={() => setSidebarAbierto(true)}
                            aria-label="Abrir menú de navegación"
                            aria-controls="admin-sidebar"
                            aria-expanded={sidebarAbierto}
                        >
                            <Menu size={20} />
                        </button>
                        <div className="admin-page-context">
                            <span>SIGODIESEL B2B / ADMINISTRACIÓN</span>
                            <strong>{seccionActual}</strong>
                        </div>
                    </div>
                    <div className="admin-topbar-user">
                        <span className="admin-topbar-status" aria-hidden="true" />
                        <span className="admin-topbar-name">{usuario?.nombre} {usuario?.apellido}</span>
                        <span className="admin-topbar-avatar" aria-hidden="true">{iniciales || "AD"}</span>
                        <ShieldCheck size={16} aria-label="Sesión autenticada" />
                    </div>
                </header>
                <div className="admin-page-content">{children}</div>
            </main>
        </div>
    );
}

export default AdminLayout;
