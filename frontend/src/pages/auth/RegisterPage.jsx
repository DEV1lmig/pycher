import { Link } from "@tanstack/react-router";
import AuthLayout from "@/components/auth/AuthLayout";

export default function RegisterPage() {
  const handleRegister = (e) => {
    e.preventDefault();
    console.log("Registrando usuario");
  };

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
      <form onSubmit={handleRegister} className="space-y-4 bg-[#1a1433]/70 p-6 rounded-lg w-[25rem]">
        <div className="mb-4">
          <label className="block text-white text-sm font-medium mb-1">Nombre</label>
          <input
            type="text"
            className="w-full border rounded-md p-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            placeholder="Ingresa tu nombre completo"
            required
          />
        </div>
        <div className="mb-4">
          <label className="block text-white text-sm font-medium mb-1">Apellido</label>
          <input
            type="text"
            className="w-full border rounded-md p-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            placeholder="Ingresa tu apellido"
            required
          />
        </div>
        <div className="mb-4">
          <label className="block text-white text-sm font-medium mb-1">Correo Electrónico</label>
          <input
            type="email"
            className="w-full border rounded-md p-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            placeholder="xxxxxxx@gmail.com"
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
          Registrarse
        </button>
      </form>
    </AuthLayout>
  );
}