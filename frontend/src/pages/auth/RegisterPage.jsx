import { useEffect } from "react";
import { useNavigate, Link } from "@tanstack/react-router";
import { isAuthenticated } from "@/lib/auth";
import AuthLayout from "@/components/auth/AuthLayout";
import { RegisterForm } from "@/components/auth/registerForm";

export default function RegisterPage() {
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated()) {
      navigate({ to: "/home" }); // or your home route
    }
  }, []);

  return (
      <AuthLayout isRegister={true}>
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white mb-2">Registrarse</h1>
        <p className="text-sm text-gray-400">
          ¿Ya tienes una cuenta?{" "}
          <Link to="/login" className="text-[#9980f2] hover:underline">
            Inicia sesión
          </Link>
        </p>
      </div>
     <RegisterForm />
    </AuthLayout>
  );
}
