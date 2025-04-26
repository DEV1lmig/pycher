import React, {useState} from 'react';
import { Link } from '@tanstack/react-router';
import logo from '../assets/img/logo.png'; 
import p_background from '../assets/img/p-background.png';
import background from '../assets/img/background.png';

export default function LandingPage() {
  const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setCursorPosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };
  
  const handleMouseLeave = () => {
    setCursorPosition({ x: -100, y: -100 }); 
  };

  return (
    <div className="relative group min-h-screen bg-white text-white">
      <div
        className="relative group overflow-hidden"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-dark to-dark-light"></div>
        <div
          className="absolute w-20 h-20 bg-primary opacity-30 rounded-full blur-xl pointer-events-none transition-transform "
          style={{
            left: `${cursorPosition.x - 30}px`, 
            top: `${cursorPosition.y - 25}px`, 
          }}
        ></div>

        <header className="relative container mx-auto px-4 py-24 text-center">
          <p className="text-lg mb-2 text-primary-light tracking-[0.3rem]">
            SOLUCIÓN A LA EDUCACIÓN
          </p>
          <h1 className="text-4xl font-bold mb-4 text-white">
            Domina el aprendizaje de Python <br /> impulsado por IA
            <span className="text-secondary">.</span>
          </h1>
          <p className="text-lg mb-6 text-tertiary">
            Obtén al instante feedback y guía personalizada.
          </p>
          <Link
            to="/register"
            className="bg-primary hover:bg-primary-opaque text-white font-medium py-3 px-6 rounded-full transition-colors"
          >
            Comienza Gratis
          </Link>
          <img src={logo} alt="logo" className="mx-auto w-12 h-auto m-10" />
        </header>
      </div>



      {/* Courses Section */}
      <section className="container mx-auto px-24 py-12 -mt-36 relative z-10">
        <div className="grid md:grid-cols-3 gap-24">
          {/* Course Card 1 */}
          <div className="bg-white text-black p-6 rounded-lg shadow-xl transform transition-transform hover:scale-105">
            <img src={p_background} alt="p-background"/>
            <h3 className="text-xl font-bold mt-4 mb-2 text-dark">Curso básico de Python</h3>
            <p className="text-sm mb-4">23 Lecciones • 1 hr 30 min</p>
            <p className="text-sm mb-4">Con Inteligencia Artificial integrada</p>
            <p className="text-sm font-bold">Prof. 1</p>
          </div>

          {/* Course Card 2 */}
          <div className="bg-white text-black p-6 rounded-lg shadow-xl transform transition-transform hover:scale-105">
          <img src={p_background} alt="p-background"/>
            <h3 className="text-xl font-bold mt-4 mb-2 text-dark">Curso intermedio de Python</h3>
            <p className="text-sm mb-4">16 Lecciones • 1 hr 10 min</p>
            <p className="text-sm mb-4">Con Inteligencia Artificial integrada</p>
            <p className="text-sm font-bold">Prof. 2</p>
          </div>

          {/* Course Card 3 */}
          <div className="bg-white text-black p-6 rounded-lg shadow-xl transform transition-transform hover:scale-105">
          <img src={p_background} alt="p-background"/>
            <h3 className="text-xl font-bold mt-4 mb-2 text-dark">Curso avanzado de Python</h3>
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
      <section 
      className="container mx-auto px-4 py-12 grid md:grid-cols-2 gap-8 items-center"
      style={{backgroundImage: `url(${background})`, backgroundSize: 'cover', backgroundPosition: 'center'}}>
        <div>
        <h2 className="text-3xl font-bold mb-4 text-white relative">
          Registra tu <span className="relative z-10">Cuenta </span>
          <span className="absolute inset-0 w-20 h-2 bg-primary -bottom-1 left-48 z-0"></span>
          GRATIS para<br />
          acceder a <span className='text-secondary'>300</span> cursos online
        </h2>
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
