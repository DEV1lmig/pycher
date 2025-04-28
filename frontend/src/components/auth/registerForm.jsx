"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { registerUser } from "@/services/userService";
import { toast } from "react-hot-toast"

export function RegisterForm() {
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
  })
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await registerUser(formData);
      toast.success("Registro exitoso. Ahora puedes iniciar sesión.");
      // Optionally redirect to login page
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar usuario.");
    } finally {
      setLoading(false);
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleCheckboxChange = (checked) => {
    setFormData((prev) => ({ ...prev, acceptTerms: checked }))
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="firstName" className="text-white">
            Nombre
          </Label>
          <Input
            id="firstName"
            name="firstName"
            value={formData.firstName}
            onChange={handleChange}
            placeholder="Nombre"
            className="bg-[#1a1433] border-[#312a56] text-white"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="lastName" className="text-white">
            Apellido
          </Label>
          <Input
            id="lastName"
            name="lastName"
            value={formData.lastName}
            onChange={handleChange}
            placeholder="Apellido"
            className="bg-[#1a1433] border-[#312a56] text-white"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="username" className="text-white">
            Username
          </Label>
          <Input
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="Username"
            className="bg-[#1a1433] border-[#312a56] text-white"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email" className="text-white">
            Correo electrónico
          </Label>
          <Input
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Correo electrónico"
            className="bg-[#1a1433] border-[#312a56] text-white"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="password" className="text-white">
            Contraseña
          </Label>
          <Input
            id="password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Contraseña"
            className="bg-[#1a1433] border-[#312a56] text-white"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirmPassword" className="text-white">
            Repetir Contraseña
          </Label>
          <Input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Repetir Contraseña"
            className="bg-[#1a1433] border-[#312a56] text-white"
          />
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox
          id="terms"
          checked={formData.acceptTerms}
          onCheckedChange={handleCheckboxChange}
          className="border-[#312a56] data-[state=checked]:bg-[#5f2dee]"
        />
        <label
          htmlFor="terms"
          className="text-sm font-medium leading-none text-white peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          Acepto los términos y Políticas de Privacidad
        </label>
      </div>
      <Button type="submit" className="w-full bg-[#5f2dee] hover:bg-[#4f25c5] text-white" disabled={loading}>
        {loading ? "Registrando..." : "Registrarse"}
      </Button>
    </form>
  )
}
