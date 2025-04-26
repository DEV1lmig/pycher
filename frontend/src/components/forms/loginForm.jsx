"use client"

import { useState } from "react"
import { Link } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

export function LoginForm() {
  const [formData, setFormData] = useState({
    emailUsername: "",
    password: "",
    remember: false,
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log("Login form submitted:", formData)
    // Handle login logic here
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
        <Label htmlFor="emailUsername" className="text-white">
          Username o Correo Electrónico
        </Label>
        <Input
          id="emailUsername"
          name="emailUsername"
          value={formData.emailUsername}
          onChange={handleChange}
          placeholder="Tu username o correo electrónico"
          className="bg-[#1a1433] border-[#312a56] text-white"
        />
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
          className="bg-[#1a1433] border-[#312a56] text-white"
        />
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
