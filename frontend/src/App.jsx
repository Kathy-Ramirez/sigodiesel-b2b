
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Vehiculos from "./pages/Vehiculos";
import { useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Empresas from "./pages/Empresas";
import Transportistas from "./pages/Transportistas";
import Cupos from "./pages/Cupos";

function App() {
    const { autenticado, usuario } = useAuth();

    if (!autenticado) {
        return <Login />;
    }

    if (usuario?.rol !== "ADMINISTRADOR") {
        return <Login />;
    }

    return (
        <BrowserRouter>
            <Routes>
                <Route path="/admin" element={<Dashboard />} />
                <Route path="/admin/empresas" element={<Empresas />} />
                <Route path="/admin/vehiculos" element={<Vehiculos />} />
                <Route path="/admin/transportistas" element={<Transportistas />}/>
                <Route path="/admin/cupos" element={<Cupos />} />

                <Route
                    path="*"
                    element={<Navigate to="/admin" replace />}
                />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
