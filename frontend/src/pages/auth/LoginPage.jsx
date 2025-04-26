import AuthLayout from "@/components/layout/AuthLayout"
import { AuthTabs } from "@/components/modules/AuthTabs"
import { LoginForm } from "@/components/forms/loginForm"

export default function LoginPage() {
  return (
    <AuthLayout>
      <AuthTabs />
      {/* Form Title */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white mb-2">Inicio de Sesión</h1>
        <p className="text-sm text-gray-400">
          ¿No tienes una cuenta todavía?{" "}
          <a href="/register" className="text-[#9980f2] hover:underline">
            Regístrate gratis
          </a>
        </p>
      </div>

      {/* Form */}
      <div className="space-y-4 bg-[#1a1433]/70 p-6 rounded-lg">
        <LoginForm />
      </div>
    </AuthLayout>
  )
}
