"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { registerUser } from "@/services/userService"
import { toast } from "react-hot-toast"
import { registerSchema } from "@/lib/schemas" // <-- Import schema

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
  const [formErrors, setFormErrors] = useState({})
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = registerSchema.safeParse(formData)
    if (!result.success) {
      setFormErrors(result.error.format())
      setLoading(false)
      return
    }
    setFormErrors({})
    setLoading(true);
    try {
      // Map camelCase to snake_case
      const payload = {
        first_name: formData.firstName,
        last_name: formData.lastName,
        username: formData.username,
        email: formData.email,
        password: formData.password,
        accept_terms: formData.acceptTerms,
      };
      await registerUser(payload);
      toast.success("Registro exitoso. Ahora puedes iniciar sesión.");
      // Optionally redirect to login page
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
        // Handles {"detail": "Email already registered"}
        toast.error(detail.detail);
      } else if (typeof detail === "object" && detail?.msg) {
        toast.error(detail.msg);
      } else if (detail) {
        toast.error(JSON.stringify(detail));
      } else {
        toast.error("Error al registrar usuario.");
      }
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
            className={`bg-[#1a1433] border-[#312a56] text-white ${formErrors.firstName ? "border-red-500" : ""}`}
          />
          {formErrors.firstName && (
            <span className="text-red-500 text-xs">{formErrors.firstName._errors[0]}</span>
          )}
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
            className={`bg-[#1a1433] border-[#312a56] text-white ${formErrors.lastName ? "border-red-500" : ""}`}
          />
          {formErrors.lastName && (
            <span className="text-red-500 text-xs">{formErrors.lastName._errors[0]}</span>
          )}
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
            className={`bg-[#1a1433] border-[#312a56] text-white ${formErrors.username ? "border-red-500" : ""}`}
          />
          {formErrors.username && (
            <span className="text-red-500 text-xs">{formErrors.username._errors[0]}</span>
          )}
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
            className={`bg-[#1a1433] border-[#312a56] text-white ${formErrors.email ? "border-red-500" : ""}`}
          />
          {formErrors.email && (
            <span className="text-red-500 text-xs">{formErrors.email._errors[0]}</span>
          )}
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
            className={`bg-[#1a1433] border-[#312a56] text-white ${formErrors.password ? "border-red-500" : ""}`}
          />
          {formErrors.password && (
            <span className="text-red-500 text-xs">{formErrors.password._errors[0]}</span>
          )}
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
            className={`bg-[#1a1433] border-[#312a56] text-white ${formErrors.confirmPassword ? "border-red-500" : ""}`}
          />
          {formErrors.confirmPassword && (
            <span className="text-red-500 text-xs">{formErrors.confirmPassword._errors[0]}</span>
          )}
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
      {formErrors.acceptTerms && (
        <span className="text-red-500 text-xs block">{formErrors.acceptTerms._errors[0]}</span>
      )}
      <Button type="submit" className="w-full bg-[#5f2dee] hover:bg-[#4f25c5] text-white" disabled={loading}>
        {loading ? "Registrando..." : "Registrarse"}
      </Button>
    </form>
  )
}
