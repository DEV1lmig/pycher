import React from 'react';
import { Link } from '@tanstack/react-router';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-dark-background text-white">
      {/* Header Section */}
      <header className="container mx-auto px-4 py-8 text-center">
        <h1 className="text-4xl font-bold mb-4 text-primary">Domina el aprendizaje de Python impulsado por IA</h1>
        <p className="text-lg mb-6 text-primary-light">Obtén al instante feedback y guía personalizada.</p>
        <Link
          to="/register"
          className="bg-primary hover:bg-primary-light text-white font-medium py-3 px-6 rounded-md transition-colors"
        >
          Comienza Gratis
        </Link>
      </header>

      {/* Courses Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="grid md:grid-cols-3 gap-8">
          {/* Course Card 1 */}
          <div className="bg-white text-black p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-bold mb-2 text-dark">Curso básico de Python</h3>
            <p className="text-sm mb-4">23 Lecciones • 1 hr 30 min</p>
            <p className="text-sm mb-4">Con Inteligencia Artificial integrada</p>
            <p className="text-sm font-bold">Prof. 1</p>
          </div>

          {/* Course Card 2 */}
          <div className="bg-white text-black p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-bold mb-2 text-dark">Curso intermedio de Python</h3>
            <p className="text-sm mb-4">16 Lecciones • 1 hr 10 min</p>
            <p className="text-sm mb-4">Con Inteligencia Artificial integrada</p>
            <p className="text-sm font-bold">Prof. 2</p>
          </div>

          {/* Course Card 3 */}
          <div className="bg-white text-black p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-bold mb-2 text-dark">Curso avanzado de Python</h3>
            <p className="text-sm mb-4">29 Lecciones • 2 hr 30 min</p>
            <p className="text-sm mb-4">Con Inteligencia Artificial integrada</p>
            <p className="text-sm font-bold">Prof. 3</p>
          </div>
        </div>
      </section>

      {/* Statistics Section */}
      <section className="bg-dark py-12">
        <div className="container mx-auto px-4 text-center grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-3xl font-bold text-secondary">27+</h3>
            <p>Certificados Totales</p>
          </div>
          <div>
            <h3 className="text-3xl font-bold text-secondary">145+</h3>
            <p>Estudiantes Totales</p>
          </div>
          <div>
            <h3 className="text-3xl font-bold text-secondary">10k+</h3>
            <p>Registros Totales</p>
          </div>
          <div>
            <h3 className="text-3xl font-bold text-secondary">10+</h3>
            <p>Por el Mundo</p>
          </div>
        </div>
      </section>

      {/* Registration Section */}
      <section className="container mx-auto px-4 py-12 grid md:grid-cols-2 gap-8 items-center">
        <div>
          <h2 className="text-2xl font-bold mb-4 text-primary">Registra tu Cuenta GRATIS</h2>
          <p className="mb-4 text-primary-light">Accede hasta 300 cursos online.</p>
          <p>Aprende a manejar Python con Inteligencia Artificial en un solo paso.</p>
        </div>
        <div className="bg-white text-black p-6 rounded-lg shadow-md">
          <form>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1">Tu Nombre Completo</label>
              <input
                type="text"
                className="w-full border rounded-md p-2"
                placeholder="Ingresa tu nombre completo"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1">Teléfono</label>
              <input
                type="text"
                className="w-full border rounded-md p-2"
                placeholder="Ingresa tu teléfono"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1">Correo Electrónico</label>
              <input
                type="email"
                className="w-full border rounded-md p-2"
                placeholder="Ingresa tu correo electrónico"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1">Contraseña</label>
              <input
                type="password"
                className="w-full border rounded-md p-2"
                placeholder="Crea una contraseña"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-primary hover:bg-primary-light text-white font-medium py-2 px-4 rounded-md"
            >
              Registrarse
            </button>
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-dark py-6 text-center text-white">
        <p>© 2025 Pycher. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}
