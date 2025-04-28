import logo from "@/assets/img/logo.png"

export default function AuthLayout({ children }) {
  return (
    <main className="flex min-h-screen">
      <div className="hidden md:flex md:w-1/2 bg-gradient-to-br from-[#160f30] via-[#312a56] to-[#312a56] items-center justify-center p-10">
        <div className="text-center">
          <div className="text-white text-4xl font-bold mb-8 flex items-center justify-center">
            <span className="mr-2">{"</ >"}</span> PyCher
          </div>
          {/* Desktop Logo */}
          <div className="w-48 h-48 mx-auto flex items-center justify-center">
            <img src={logo} alt="PyCher Logo" className="w-48 h-48 object-contain" />
          </div>
        </div>
      </div>
      <div className="w-full md:w-1/2 bg-[#160f30] flex items-center justify-center p-4">
        <div className="w-full max-w-md space-y-6">
          {/* Mobile Logo */}
          <div className="md:hidden text-center mb-8">
            <div className="text-white text-3xl font-bold mb-4 flex items-center justify-center">
              <span className="mr-2">{"</ >"}</span> PyCher
            </div>
            <div className="w-24 h-24 mx-auto flex items-center justify-center">
              <img src={logo} alt="PyCher Logo" className="w-24 h-24 object-contain" />
            </div>
          </div>
          {children}
        </div>
      </div>
    </main>
  )
}
