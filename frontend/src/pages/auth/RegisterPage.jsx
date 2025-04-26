import AuthLayout from "@/components/layout/AuthLayout"
import { AuthTabs } from "@/components/modules/AuthTabs"
import { RegisterForm } from "@/components/forms/registerForm"

export default function RegisterPage() {
  return (
    <AuthLayout>
      <AuthTabs />

      {/* Form Title */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white mb-2">Registrarse</h1>
        <p className="text-sm text-gray-400">
          ¿Ya tienes una cuenta?{" "}
          <a href="/login" className="text-[#9980f2] hover:underline">
            Inicia sesión
          </a>
        </p>
      </div>

      {/* Form */}
      <div className="space-y-4 bg-[#1a1433]/70 p-6 rounded-lg">
        <RegisterForm />
      </div>
    </AuthLayout>
  )
}
