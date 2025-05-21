import { useEffect, useState } from "react";
import { getUserProfile } from "../../services/userService";
import { Input } from "../../components/ui/input";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import Waves from "@/components/ui/waves";
import { FiUser, FiEye, FiEyeOff } from "react-icons/fi";
import { Link } from '@tanstack/react-router';
import FadeContent from "../../components/ui/fade-content.jsx";

export default function ProfilePage() {
  const [user, setUser] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showRepeat, setShowRepeat] = useState(false);

  useEffect(() => {
    getUserProfile().then(setUser)
  }, [])

  return (
    <DashboardLayout>
    <div className="relative w-full min-h-[calc(100vh-4rem)]"> 
        <FadeContent blur={true} duration={300} easing="ease-out" initialOpacity={1}>
        <div className="relative w-full h-80 min-w-0">
            <Waves
              lineColor="rgba(152, 128, 242, 0.5)"
              backgroundColor="#160f30"
              waveSpeedX={0.02}
              waveSpeedY={0.01}
              waveAmpX={70}
              waveAmpY={20}
              friction={0.9}
              tension={0.01}
              maxCursorMove={60}
              xGap={12}
              yGap={36}
            />
            <div className="relative flex items-center justify-center w-full h-80">
            <h2 className="z-10 opacity-80 text-4xl font-bold text-center px-2 mb-12 mix-blend-lighten">
                Editar Perfil
            </h2>
            </div>
        </div>
        </FadeContent>

      <div
        className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 
        bg-dark/90 min-h-[25rem] w-full max-w-xl md:max-w-2xl lg:max-w-3xl min:mx-6 rounded-xl 
        flex flex-col justify-center gap-4 z-10"
        style={{ top: "50%" }}
      >
        <div className="flex my-6 flex-col gap-8 p-4">
          <div className="absolute left-1/2 -top-12 transform -translate-x-1/2 z-20">
            <div className="bg-primary flex items-center justify-center rounded-full w-24 h-24 shadow-lg border-4 border-dark/90">
              <FiUser className="text-white text-5xl" />
            </div>
          </div>
          <p className="flex justify-center items-center mt-4 text-xl">
            ¿Qué información cambiaremos el día de hoy?
          </p>
          <div className="flex flex-col md:flex-row gap-4 mt-2">
            <Input
              type="text"
              value={user ? `${user.first_name}` : "Carlos"}
              placeholder="Nombre"
              onChange
              className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md"
            />
            <Input
              type="text"
              value={user ? `${user.last_name}` : "Rodríguez"}
              placeholder="Apellido"
              onChange
              className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md"
            />
          </div>

          <Input
            type="email"
            value={user ? `${user.email}` : "xxxxx@gmail.com"}
            placeholder="Correo electrónico"
            onChange
            className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md"
          />

          <div className="flex flex-col md:flex-row gap-4 w-full">
            <div className="relative w-full">
              <Input
                type={showPassword ? "text" : "password"}
                placeholder="Contraseña"
                onChange
                className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md pr-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xl text-gray-400 hover:text-primary focus:outline-none"
                onClick={() => setShowPassword((v) => !v)}
                tabIndex={-1}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
            <div className="relative w-full">
              <Input
                type={showRepeat ? "text" : "password"}
                placeholder="Repetir Contraseña"
                onChange
                className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md pr-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xl text-gray-400 hover:text-primary focus:outline-none"
                onClick={() => setShowRepeat((v) => !v)}
                tabIndex={-1}
              >
                {showRepeat ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
          </div>

          <div className="flex justify-center">
            <Link
              to="/profile"
              className="block p-2 bg-secondary text-center hover:bg-secondary/70 text-dark cursor-pointer w-52 rounded-xl text-base font-semibold"
            >
              Guardar
            </Link>
          </div>
        </div>
      </div>
    </div>
    </DashboardLayout>
  );
}