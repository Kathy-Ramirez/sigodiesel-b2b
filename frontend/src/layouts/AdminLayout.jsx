
import { LayoutDashboard, Building2, Truck, Users, Fuel, ClipboardList, History, UserCog, 
    LogOut,} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function AdminLayout({ children }) {
    const { usuario, cerrarSesion } = useAuth();

    const opcionesMenu = [
        { nombre: "Inicio", ruta: "/admin", icono: LayoutDashboard },
        { nombre: "Empresas", ruta: "/admin/empresas", icono: Building2 },
        { nombre: "Vehículos", ruta: "/admin/vehiculos", icono: Truck },
        { nombre: "Transportistas", ruta: "/admin/transportistas", icono: Users },
        { nombre: "Estaciones", ruta: "/admin/estaciones", icono: Fuel },
        { nombre: "Historial de despachos", ruta: "/admin/historial-despachos", icono: ClipboardList },
        { nombre: "Usuarios", ruta: "/admin/usuarios", icono: UserCog },
        { nombre: "Cupos semanales", ruta: "/admin/cupos", icono: Fuel,}
    ];

    return (
        <div className="admin-layout">
            <aside className="sidebar">

                <div className="sidebar-logo">
                    <h2>SIGODIESEL</h2>
                    <span>B2B ADMINISTRACIÓN</span>
                </div>

                <nav className="sidebar-menu">
                    <p className="menu-titulo">MENÚ PRINCIPAL</p>

                    {opcionesMenu.map((opcion) => {
                        const Icono = opcion.icono;

                        return (
                            <NavLink
                                to={opcion.ruta}
                                key={opcion.nombre}
                                end={opcion.ruta === "/admin"}
                                className={({ isActive }) =>
                                    isActive
                                        ? "menu-item menu-item-activo"
                                        : "menu-item"
                                }
                            >
                                <Icono size={20} />
                                <span>{opcion.nombre}</span>
                            </NavLink>
                        );
                    })}
                </nav>

                <div className="sidebar-footer">
                    <div className="usuario-info">
                        <strong>
                            {usuario?.nombre} {usuario?.apellido}
                        </strong>
                        <span>Administrador</span>
                    </div>

                    <button
                        className="btn-cerrar-sesion"
                        onClick={cerrarSesion}
                    >
                        <LogOut size={18} />
                        Cerrar sesión
                    </button>
                </div>

            </aside>

            <main className="admin-contenido">
                {children}
            </main>
        </div>
    );
}

export default AdminLayout;
