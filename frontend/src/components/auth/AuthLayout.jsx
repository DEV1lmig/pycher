import { useState } from "react";
import logo from "@/assets/img/logo.png";
import { LoginForm } from "@/components/auth/loginForm";
import { RegisterForm } from "@/components/auth/registerForm";

export default function AuthLayout() {
  const [isRegister, setIsRegister] = useState(false); 
  const [showRegister, setShowRegister] = useState(false);

  const handleToggle = () => {
    setIsRegister((prev) => !prev);

    setTimeout(() => {
      setShowRegister((prev) => !prev);
    }, 280); 
  };

  return (
    <main className="relative flex min-h-screen overflow-hidden bg-dark">
      <div
        className={`relative z-10 hidden md:flex md:w-1/2 bg-gradient-to-br from-[#160f30] via-[#312a56] to-[#312a56] items-center justify-center p-10 transition-all duration-700 ${
          isRegister ? "translate-x-full" : "translate-x-0"
        }`}
      >
        <div className="text-center">
          <div className="text-white text-4xl font-bold mb-8 flex items-center justify-center">
            <span className="mr-2">{"</ >"}</span> PyCher
          </div>
          <div className="w-48 h-48 mx-auto flex items-center justify-center">
            <img src={logo} alt="PyCher Logo" className="w-48 h-48 object-contain" />
          </div>
        </div>
      </div>

      <div
        className={`w-full md:w-1/2 bg-[#160f30] flex items-center justify-center p-4 transition-all duration-700 ${
          isRegister ? "-translate-x-full" : "translate-x-0"
        }`}
      >
        <div className="w-full max-w-md space-y-6">
          {/* Mobile Logo */}
          <div className="md:hidden text-center mb-8">
            <div className="text-white text-3xl font-bold mb-4 flex items-center justify-center">
              <span className="mr-2">{"</ >"}</span> PyCher
            </div>
            <div className="w-24 h-24 mx-auto flex items-center justify-center">
              <img src={logo} alt="PyCher Logo" className="w-24 h-24 object-contain" />
            </div>
          </div>

          {showRegister ? (
            <>
              <div className="text-center">
                <h1 className="text-2xl font-bold text-white mb-2">Registrarse</h1>
                <p className="text-sm text-gray-400">
                  ¿Ya tienes una cuenta?{" "}
                  <button
                    onClick={handleToggle} 
                    className="text-[#9980f2] hover:underline"
                  >
                    Inicia sesión
                  </button>
                </p>
              </div>
              <div className="space-y-4 bg-[#1a1433]/70 p-6 rounded-lg">
                <RegisterForm />
              </div>
            </>
          ) : (
            <>
              <div className="text-center">
                <h1 className="text-2xl font-bold text-white mb-2">Inicio de Sesión</h1>
                <p className="text-sm text-gray-400">
                  ¿No tienes una cuenta todavía?{" "}
                  <button
                    onClick={handleToggle} 
                    className="text-[#9980f2] hover:underline"
                  >
                    Regístrate gratis
                  </button>
                </p>
              </div>
              <div className="space-y-4 bg-[#1a1433]/70 p-6 rounded-lg">
                <LoginForm />
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}