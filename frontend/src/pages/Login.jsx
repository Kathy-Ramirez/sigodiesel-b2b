
import { useState } from "react";
import { useAuth } from "../context/AuthContext";

function Login() {
    const { iniciarSesion } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [cargando, setCargando] = useState(false);

    const manejarLogin = async (e) => {
        e.preventDefault();
        setError("");
        setCargando(true);

        try {
            const usuario = await iniciarSesion(email, password);

            if (usuario.rol !== "ADMINISTRADOR") {
                setError("Este acceso es exclusivo para administradores.");
            }
        } catch (err) {
            setError(
                err.response?.data?.error ||
                "No se pudo iniciar sesión. Verifica tus datos."
            );
        } finally {
            setCargando(false);
        }
    };

    return (
        <div>
            <h1>SIGODIESEL B2B</h1>
            <h2>Iniciar sesión</h2>

            <form onSubmit={manejarLogin}>
                <div>
                    <label>Correo electrónico</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>

                <div>
                    <label>Contraseña</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>

                {error && <p style={{ color: "red" }}>{error}</p>}

                <button type="submit" disabled={cargando}>
                    {cargando ? "Ingresando..." : "Ingresar"}
                </button>
            </form>
        </div>
    );
}

export default Login;
