
import AdminLayout from "../layouts/AdminLayout";

function Dashboard() {
    return (
        <AdminLayout>
            <div className="dashboard-header">
                <h1>Panel administrativo</h1>
                <p>
                    Bienvenido al sistema de gestión SIGODIESEL B2B.
                </p>
            </div>

            <div className="dashboard-contenido">
                <h2>Resumen general</h2>
                <p>
                    Desde aquí podrás administrar las empresas,
                    vehículos, transportistas, estaciones y cupos
                    semanales.
                </p>
            </div>
        </AdminLayout>
    );
}

export default Dashboard;
