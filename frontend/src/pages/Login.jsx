import { useState } from "react";
import { Eye, EyeOff, LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import "../estilos/login.css";

function Login() {
    const { iniciarSesion } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [cargando, setCargando] = useState(false);
    const [mostrarPassword, setMostrarPassword] = useState(false);

    const manejarLogin = async (e) => {
        e.preventDefault(); setError(""); setCargando(true);
        try {
            const usuario = await iniciarSesion(email, password);
            if (usuario.rol !== "ADMINISTRADOR" && usuario.rol !== "TRANSPORTISTA") setError("Este acceso no está habilitado para este rol.");
        } catch (err) {
            setError(err.response?.data?.error || "No se pudo iniciar sesión. Verifica tus datos.");
        } finally { setCargando(false); }
    };

    return <main className="login-shell">
        <section className="login-brand-panel"><div className="login-brand-mark"><ShieldCheck size={26} /></div><p className="login-eyebrow">PLATAFORMA B2B</p><h1>SIGODIESEL<span>B2B</span></h1><p className="login-brand-copy">Control inteligente y seguro para la gestión de cupos de diésel.</p><div className="login-brand-line" /><small>Gestión · Control · Trazabilidad</small></section>
        <section className="login-card"><div className="login-card-heading"><p className="login-eyebrow">BIENVENIDO</p><h2>Iniciar sesión</h2><p>Ingresa tus credenciales para continuar.</p></div><form onSubmit={manejarLogin} className="login-form">
            <label className="login-field"><span>Correo electrónico</span><div className="login-input-wrap"><Mail size={18} /><input type="email" placeholder="nombre@empresa.com" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required /></div></label>
            <label className="login-field"><span>Contraseña</span><div className="login-input-wrap"><LockKeyhole size={18} /><input type={mostrarPassword ? "text" : "password"} placeholder="Ingresa tu contraseña" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /><button type="button" className="login-password-toggle" onClick={() => setMostrarPassword((visible) => !visible)} aria-label={mostrarPassword ? "Ocultar contraseña" : "Mostrar contraseña"}>{mostrarPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
            {error && <div className="login-error" role="alert">{error}</div>}
            <button className="login-submit" type="submit" disabled={cargando}>{cargando ? <><span className="login-spinner" /> Ingresando...</> : "Ingresar al sistema"}</button>
        </form><p className="login-footer">Acceso protegido · SIGODIESEL B2B</p></section>
    </main>;
}

export default Login;
