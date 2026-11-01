import { createContext, useContext, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [usuario, setUsuario] = useState(() => {
        const usuarioGuardado = localStorage.getItem("usuario");

        return usuarioGuardado
            ? JSON.parse(usuarioGuardado)
            : null;
    });

    const [token, setToken] = useState(() => {
        return localStorage.getItem("access_token");
    });

    const iniciarSesion = async (email, password) => {
        const respuesta = await api.post("/auth/login", {
            email,
            password,
        });

        const { access_token, usuario } = respuesta.data;
        // temporalmente 
        console.log("Usuario autenticado:", usuario); 

        localStorage.setItem("access_token", access_token);
        localStorage.setItem("usuario", JSON.stringify(usuario));

        setToken(access_token);
        setUsuario(usuario);

        return usuario;
    };

    const cerrarSesion = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("usuario");

        setToken(null);
        setUsuario(null);
    };

    return (
        <AuthContext.Provider
            value={{
                usuario,
                token,
                autenticado: Boolean(token),
                iniciarSesion,
                cerrarSesion,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
