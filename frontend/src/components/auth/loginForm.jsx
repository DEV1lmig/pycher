"use client"

import { useState } from "react"
import { Link } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { loginUser } from "@/services/userService"
import { toast } from "react-hot-toast"
import { useNavigate } from "@tanstack/react-router"
import { loginSchema } from "@/lib/schemas" // <-- Import schema

export function LoginForm() {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    remember: false,
  })
  const [formErrors, setFormErrors] = useState({})
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = loginSchema.safeParse(formData)
    if (!result.success) {
      setFormErrors(result.error.format())
      return
    }
    setFormErrors({})
    try {
      await loginUser({
        username: formData.username,
        password: formData.password,
      })
      toast.success("Inicio de sesión exitoso.")
      navigate({ to: "/home"})
    } catch (error) {
      const detail = error.response?.data?.detail;
      const errors = Array.isArray(detail)
        ? detail
        : (error.response?.status === 422 && Array.isArray(error.response?.data?.detail))
          ? error.response.data.detail
          : null;

      if (typeof detail === "string") {
        toast.error(detail);
      } else if (errors) {
        errors.forEach((err) => {
          if (err.msg) {
            toast.error(err.msg);
          } else if (typeof err === "string") {
            toast.error(err);
          } else {
            toast.error(JSON.stringify(err));
          }
        });
      } else if (typeof detail === "object" && detail !== null && typeof detail.detail === "string") {
        toast.error(detail.detail);
      } else if (typeof detail === "object" && detail?.msg) {
        toast.error(detail.msg);
      } else if (detail) {
        toast.error(JSON.stringify(detail));
      } else {
        toast.error("Error al iniciar sesión. Verifica tus credenciales.");
      }
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleCheckboxChange = (checked) => {
    setFormData((prev) => ({ ...prev, remember: checked }))
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="space-y-2">
        <Label htmlFor="username" className="text-white">
          Username o Correo Electrónico
        </Label>
        <Input
          id="username"
          name="username"
          value={formData.username}
          onChange={handleChange}
          placeholder="Tu username o correo electrónico"
          className={`bg-[#1a1433] border-[#312a56] text-white ${formErrors.username ? "border-red-500" : ""}`}
        />
        {formErrors.username && (
          <span className="text-red-500 text-xs">{formErrors.username._errors[0]}</span>
        )}
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="password" className="text-white">
            Contraseña
          </Label>
          <Link href="#" className="text-xs text-[#9980f2] hover:underline">
            ¿Olvidaste tu contraseña?
          </Link>
        </div>
        <Input
          id="password"
          name="password"
          type="password"
          value={formData.password}
          onChange={handleChange}
          placeholder="Contraseña"
          className={`bg-[#1a1433] border-[#312a56] text-white ${formErrors.password ? "border-red-500" : ""}`}
        />
        {formErrors.password && (
          <span className="text-red-500 text-xs">{formErrors.password._errors[0]}</span>
        )}
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox
          id="remember"
          checked={formData.remember}
          onCheckedChange={handleCheckboxChange}
          className="border-[#312a56] data-[state=checked]:bg-[#5f2dee]"
        />
        <label
          htmlFor="remember"
          className="text-sm font-medium leading-none text-white peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          Recuérdame
        </label>
      </div>
      <Button type="submit" className="w-full bg-[#5f2dee] hover:bg-[#4f25c5] text-white">
        Iniciar Sesión
      </Button>
    </form>
  )
}
