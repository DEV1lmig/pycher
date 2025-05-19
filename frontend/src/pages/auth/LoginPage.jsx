import { useEffect } from "react";
import { useNavigate, Link } from "@tanstack/react-router";
import { isAuthenticated } from "@/lib/auth"; // Your auth util
import AuthLayout from "@/components/auth/AuthLayout";
import { LoginForm } from "@/components/auth/loginForm";

export default function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated()) {
      navigate({ to: "/home" });
    }
  }, []);

  return (
    <AuthLayout isRegister={false}>
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white mb-2">Inicio de Sesión</h1>
        <p className="text-sm text-gray-400">
          ¿No tienes una cuenta todavía?{" "}
          <Link to="/register" className="text-[#9980f2] hover:underline">
            Regístrate gratis
          </Link>
        </p>
      </div>
      <LoginForm />
    </AuthLayout>
  );
}
