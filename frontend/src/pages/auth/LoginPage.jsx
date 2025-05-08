import { Link } from "@tanstack/react-router";
import AuthLayout from "@/components/auth/AuthLayout";

export default function LoginPage() {
  const handleLogin = (e) => {
    e.preventDefault();
    console.log("Iniciando sesión...");
  };

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
      <form onSubmit={handleLogin} className="space-y-4 bg-[#1a1433]/70 p-6 rounded-lg">
        <div className="mb-4">
          <label className="block text-white text-sm font-medium mb-1">Correo Electrónico</label>
          <input
            type="email"
            className="w-full border rounded-md p-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            placeholder="xxxxx@gmail.com"
            required
          />
        </div>
        <div className="mb-4">
          <label className="block text-white text-sm font-medium mb-1">Contraseña</label>
          <input
            type="password"
            className="w-full border rounded-md p-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            placeholder="●●●●●●●●"
            required
          />
        </div>
        <button
          type="submit"
          className="w-full bg-primary hover:bg-primary-light text-white font-medium py-2 px-4 rounded-md"
        >
          Iniciar Sesión
        </button>
      </form>
    </AuthLayout>
  );
}