import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Vehiculos from "./pages/Vehiculos";
import { useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Empresas from "./pages/Empresas";
import Transportistas from "./pages/Transportistas";
import Cupos from "./pages/Cupos";
import HistorialDespachos from "./pages/HistorialDespachos";
import TransportistaPortal from "./pages/TransportistaPortal";
import Estaciones from "./pages/Estaciones";
import Usuarios from "./pages/Usuarios";

function App() {
    const { autenticado, usuario } = useAuth();
    const rol = usuario?.rol?.toUpperCase();

    return (
        <BrowserRouter>
            {!autenticado ? (
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
            ) : rol === "TRANSPORTISTA" ? (
                <Routes>
                    <Route path="/transportista" element={<TransportistaPortal />} />
                    <Route path="*" element={<Navigate to="/transportista" replace />} />
                </Routes>
            ) : rol === "ADMINISTRADOR" ? (
                <Routes>
                    <Route path="/admin" element={<Dashboard />} />
                    <Route path="/admin/empresas" element={<Empresas />} />
                    <Route path="/admin/vehiculos" element={<Vehiculos />} />
                    <Route path="/admin/transportistas" element={<Transportistas />} />
                    <Route path="/admin/cupos" element={<Cupos />} />
                    <Route path="/admin/historial-despachos" element={<HistorialDespachos />} />
                    <Route path="/admin/estaciones" element={<Estaciones />} />
                    <Route path="/admin/usuarios" element={<Usuarios />} />
                    
                    <Route path="*" element={<Navigate to="/admin" replace />} />
                </Routes>
            ) : (
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
            )}
        </BrowserRouter>
    );
}

export default App;