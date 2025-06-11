import { useEffect, useState } from "react";
import { getUserProfile, updateUsername, updatePassword } from "../../services/userService";
import { Input } from "../../components/ui/input";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import Waves from "@/components/ui/waves";
import { Link } from "@tanstack/react-router";
import { FiUser, FiEye, FiEyeOff } from "react-icons/fi";
import FadeContent from "../../components/ui/fade-content.jsx";
import { loginSchema } from "@/lib/schemas"; // For username validation

export default function ProfilePage() {
  const [user, setUser] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showRepeat, setShowRepeat] = useState(false);

  // Username state
  const [username, setUsername] = useState("");
  const [usernameError, setUsernameError] = useState("");
  const [usernameSuccess, setUsernameSuccess] = useState("");

  // Password state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [repeatPassword, setRepeatPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");

  useEffect(() => {
    getUserProfile().then(u => {
      setUser(u);
      setUsername(u?.username || "");
    });
  }, []);

  // Username change handler
const handleUsernameChange = async (e) => {
  e.preventDefault();
  setUsernameError("");
  setUsernameSuccess("");

  // Prevent empty username
  if (!username.trim()) {
    setUsernameError("El nombre de usuario no puede estar vacío.");
    return;
  }
  // Prevent unchanged username
  if (user && username.trim() === user.username) {
    setUsernameError("El nombre de usuario es igual al actual.");
    return;
  }

  try {
    loginSchema.shape.username.parse(username);
    const res = await updateUsername(username);
    // If backend returns {detail: "..."}
    if (typeof res === "object" && res.detail) {
      setUsernameSuccess(res.detail);
    } else if (typeof res === "string") {
      setUsernameSuccess(res);
    } else {
      setUsernameSuccess("Usuario actualizado correctamente");
    }
  } catch (err) {
    if (err.errors) setUsernameError(err.errors[0].message);
    else if (err.response?.data?.detail) setUsernameError(err.response.data.detail);
    else if (err.detail) setUsernameError(err.detail);
    else setUsernameError("Error al actualizar usuario");
  }
};
  // Password change handler
  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");
    // Validation
    if (newPassword.length < 8) {
      setPasswordError("La contraseña debe tener al menos 8 caracteres");
      return;
    }
    if (newPassword !== repeatPassword) {
      setPasswordError("Las contraseñas no coinciden");
      return;
    }
    try {
      await updatePassword(currentPassword, newPassword);
      setPasswordSuccess("Contraseña actualizada correctamente");
      setCurrentPassword("");
      setNewPassword("");
      setRepeatPassword("");
    } catch (err) {
      if (err.response?.data?.detail) setPasswordError(err.response.data.detail);
      else setPasswordError("Error al actualizar contraseña");
    }
  };

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

        <div className="flex flex-row gap-8 items-start justify-center w-full max-w-6xl mx-auto -mt-32 z-10 relative">
          {/* Profile info card */}
          <div className="bg-dark/90 rounded-xl shadow-lg p-8 w-1/3 flex flex-col items-center min-w-[320px]">
            <div className="relative -mt-20 mb-4">
              <div className="bg-primary flex items-center justify-center rounded-full w-24 h-24 shadow-lg border-4 border-dark/90">
                <FiUser className="text-white text-5xl" />
              </div>
            </div>
            <p className="text-xl mb-6 text-center">
              Estos son tus datos.
            </p>
            <div className="flex flex-col md:flex-row gap-4 w-full mb-4">
              <Input
                type="text"
                value={user ? `${user.first_name}` : ""}
                placeholder="Nombre"
                readOnly
                className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md bg-[#2b2250]"
              />
              <Input
                type="text"
                value={user ? `${user.last_name}` : ""}
                placeholder="Apellido"
                readOnly
                className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md bg-[#2b2250]"
              />
            </div>
            <Input
              type="email"
              value={user ? `${user.email}` : ""}
              placeholder="Correo electrónico"
              readOnly
              className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md bg-[#2b2250] mb-2"
            />
          </div>

          {/* Username change card */}
          <div className="bg-dark/90 rounded-xl shadow-lg p-8 w-1/3 flex flex-col items-center min-w-[320px]">
            <form onSubmit={handleUsernameChange} className="flex flex-col gap-2 w-full max-w-md">
              <label className="font-semibold">Nombre de usuario</label>
              <Input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md"
              />
              {usernameError && <span className="text-red-400">{usernameError}</span>}
              {usernameSuccess && <span className="text-green-400">{usernameSuccess}</span>}
              <button
                type="submit"
                className="mt-2 bg-primary text-white rounded-lg px-4 py-2 font-semibold hover:bg-primary/80"
              >
                Cambiar usuario
              </button>
            </form>
          </div>

          {/* Password change card */}
          <div className="bg-dark/90 rounded-xl shadow-lg p-8 w-1/3 flex flex-col items-center min-w-[320px]">
            <form onSubmit={handlePasswordChange} className="flex flex-col gap-2 w-full max-w-md">
              <label className="font-semibold">Cambiar contraseña</label>
              <Input
                type={showPassword ? "text" : "password"}
                value={currentPassword}
                onChange={e => setCurrentPassword(e.target.value)}
                placeholder="Contraseña actual"
                className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md"
              />
              <Input
                type={showPassword ? "text" : "password"}
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                placeholder="Nueva contraseña"
                className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md"
              />
              <Input
                type={showRepeat ? "text" : "password"}
                value={repeatPassword}
                onChange={e => setRepeatPassword(e.target.value)}
                placeholder="Repetir nueva contraseña"
                className="text-white border-primary placeholder:text-white hover:border-primary/80 rounded-md"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  className="text-primary"
                  onClick={() => setShowPassword((v) => !v)}
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />} Ver contraseñas
                </button>
                <button
                  type="button"
                  className="text-primary"
                  onClick={() => setShowRepeat((v) => !v)}
                >
                  {showRepeat ? <FiEyeOff /> : <FiEye />} Ver repetir
                </button>
              </div>
              {passwordError && <span className="text-red-400">{passwordError}</span>}
              {passwordSuccess && <span className="text-green-400">{passwordSuccess}</span>}
              <button
                type="submit"
                className="mt-2 bg-primary text-white rounded-lg px-4 py-2 font-semibold hover:bg-primary/80"
              >
                Cambiar contraseña
              </button>
            </form>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
