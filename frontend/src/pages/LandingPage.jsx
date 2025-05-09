import React from 'react';
import { Link } from '@tanstack/react-router';
import NavBar from './landing/NavBar';
import logo from '../assets/img/logo.png'; 

import AnimatedContent from '../components/ui/animated-content.jsx';
import LetterGlitch from '../components/ui/letter-glitch.jsx';
import Magnet from '../components/ui/magnet.jsx';
import MetaBalls from '../components/ui/meta-balls.jsx';
import Waves from '../components/ui/waves.jsx';
import Squares from '../components/ui/squares.jsx';
import BlurText from "../components/ui/blur-text.jsx";
import TiltedCard from '../components/ui/tilted-card.jsx';
import FadeContent from '../components/ui/fade-content.jsx';
import Particles from '../components/ui/particles.jsx';
import CountUp from '../components/ui/count-up.jsx';
import Aurora from '@/components/ui/aurora';

export default function LandingPage() {
  const handleAnimationComplete = () => {
    console.log('Animation completed!');
  };

  return (
  <div className="relative group min-h-screen bg-white text-white py-">
    <NavBar />
    <div className="relative group overflow-hidden py-60">
      <div className="absolute inset-0 bg-dark">
      </div>
       <div className="absolute top-2/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10 mt-[4rem]">
        <AnimatedContent
          distance={100}
          direction="vertical"
          reverse={false}
          config={{ tension: 60, friction: 20 }}
          initialOpacity={0.2}
          animateOpacity
          scale={0.5}
          threshold={0.2}
        >
          <div className="text-8xl md:text-[250px] font-bold text-white cursor-default">
            pycher
            <span className="text-secondary">.</span>
          </div>
          
        </AnimatedContent>
    </div>

    {/* Otros elementos con sus propias animaciones */}
    <header className="relative container mx-auto px-4 py-36 text-center min-h-[500px] overflow-visible">
      <AnimatedContent
        distance={100}
        direction="vertical"
        reverse={true}
        config={{ tension: 60, friction: 20 }}
        initialOpacity={0.2}
        animateOpacity
        scale={1.5}
        threshold={0.2}
      >
        <div className="flex flex-wrap justify-center mt-8">
          {/* MetaBalls */}
          <div className="relative z-10 w-[250px] h-[250px] md:w-[200px] md:h-[200px] bg-dark overflow-hidden border-[5px] border-solid border-secondary rounded-full transition-all duration-300 ease-in-out hover:scale-95">
            <div className="absolute inset-0 transition-opacity cursor-pointer duration-300 ease-in-out hover:opacity-10">
              <MetaBalls
                color="#f2d231"
                cursorBallColor="#f2d231"
                cursorBallSize={2}
                ballCount={15}
                animationSize={30}
                enableMouseInteraction={true}
                enableTransparency={true}
                hoverSmoothness={0.05}
                clumpFactor={1}
                speed={0.3}
              />
            </div>
          </div>

          {/* Waves */}
          <div className="relative z-10 w-[250px] h-[250px] md:w-[200px] md:h-[200px] bg-dark overflow-hidden border-[5px] border-solid border-blue rounded-[30px] transition-all duration-300 ease-in-out hover:scale-95">
            <div className="absolute inset-0 transition-opacity cursor-pointer duration-300 ease-in-out hover:opacity-10">
              <Waves
                lineColor="#00B4D8"
                backgroundColor="#070113"
                waveSpeedX={0.02}
                waveSpeedY={0.01}
                waveAmpX={40}
                waveAmpY={20}
                friction={0.9}
                tension={0.01}
                maxCursorMove={120}
                xGap={12}
                yGap={36}
              />
            </div>
          </div>

          {/* Call to Action */}
          <Link
            to="/register"
            className="relative z-10 flex items-center justify-center bg-primary text-white font-medium h-[250px] w-[250px] md:h-[200px] md:w-[200px] rounded-full transition-colors"
          >
            <Magnet padding={30} disabled={false} magnetStrength={1}>
              <h1 className="transition-transform ease-in-out cursor-pointer duration-300 hover:scale-150 font-medium text-sm md:text-lg">
                Comienza <br /> Gratis
              </h1>
            </Magnet>
          </Link>

          {/* Letter Glitch */}
          <LetterGlitch
            glitchSpeed={50}
            centerVignette={true}
            outerVignette={false}
            smooth={true}
          />

          {/* Squares */}
          <div className="relative z-10 w-[250px] h-[250px] md:w-[200px] md:h-[200px] bg-dark overflow-hidden border-[5px] border-solid border-primary-light rounded-full transition-all duration-300 ease-in-out hover:scale-95">
            <div className="absolute inset-0 transition-opacity duration-300 ease-in-out hover:opacity-10">
              <Squares
                speed={0.3}
                squareSize={25}
                direction="right"
                borderColor="#8363f2"
                hoverFillColor="#222"
              />
            </div>
          </div>
        </div>
      </AnimatedContent>

      <div className='font-normal text-2xl'> 
      <div className='w-full text-left mt-12 px-36'>
  
        Obtén guía personalizada <br />
        Y feedback en <span className='text-primary'>tiempo real</span>
      </div>
      </div>
    </header>
      </div>
    
      {/* Courses Section */}
      <section className="flex flex-wrap gap-8 justify-center bg-dark mx-auto px-4">
      <div className='w-full flex justify-center items-center'>
      <BlurText
        text="Domina el aprendizaje de Python impulsado por IA"
        delay={150}
        animateBy="words"
        direction="top"
        onAnimationComplete={handleAnimationComplete}
        className="text-5xl font-bold w-[1000px] justify-center mb-8"
      />

      </div>
      

      {[...Array(3)].map((_, index) => (
        <FadeContent
          key={index}
          blur={true}
          duration={1500}
          easing="ease-out"
          initialOpacity={0}
        >
          <TiltedCard
            imageSrc="https://codigofacilito.com/covers/python-avanzado-g2/cover.png"
            altText="Curso Básico"
            containerHeight="320px"
            containerWidth="320px"
            imageHeight="250px"
            imageWidth="250px"
            rotateAmplitude={12}
            scaleOnHover={1.2}
            showMobileWarning={false}
            showTooltip={true}
            displayOverlayContent={true}
            overlayContent={
              <p className="tilted-card-demo-text ml-6 mt-6 bg-black text-white rounded-2xl px-3 py-2 bg-opacity-35">
                Curso Básico de Python
              </p>
            }
          />
        </FadeContent>
      ))}
    </section>

      <section className="bg-dark py-24 flex justify-center items-center gap-12">
      <FadeContent blur={true} duration={1200} easing="ease-out" initialOpacity={0}>
      <div className="relative w-[450px] h-[250px] bg-primary overflow-hidden border-none rounded-2xl ">
          <div className="absolute inset-0">
            <Squares
              speed={0.3}
              squareSize={30}
              direction="down" // up, down, left, right, diagonal
              borderColor="#9880f2"
              hoverFillColor="#222"
            />
          </div>

          <div className="relative z-10 flex flex-col items-start justify-end h-full ml-7">
            <div className="flex items-center text-dark text-9xl font-bold">
              <CountUp
                from={0}
                to={20}
                separator=""
                direction="up"
                duration={1}
                className="count-up-text"
              />
              <span className="text-dark">+</span>
            </div>
            <div className="text-dark text-2xl font-bold mb-5">
              Cursos Online
            </div>
          </div>
      </div>
          </FadeContent>

          <FadeContent blur={true} duration={1200} easing="ease-out" initialOpacity={0}>
          <div className="relative w-[450px] h-[250px] overflow-hidden rounded-2xl border-[1px] border-primary">

          <div className="absolute inset-0">
            <Particles
              particleColors={['#8363f2', '#9880f2']}
              particleCount={100}
              particleSpread={10}
              speed={0.2}
              particleBaseSize={160}
              moveParticlesOnHover={true}
              alphaParticles={false}
              disableRotation={false}
            />
          </div>


          <div className="relative z-10 flex flex-col items-start justify-end h-full ml-7">
            <div className="flex items-center text-primary text-9xl font-bold">
              <CountUp
                from={0}
                to={4}
                separator=""
                direction="up"
                duration={1}
                className="count-up-text"
              />
            </div>
            <div className="text-primary text-2xl font-bold mb-5">
              Certificados
            </div>
          </div>
        </div>
        </FadeContent>
      </section>

      {/* Registration Section */}
      <section className="relative bg-dark">
      <FadeContent blur={true} duration={1200} easing="ease-out" initialOpacity={1}>
      {/* Aurora como fondo absoluto */}
      <div className='relative rounded-3xl mx-24 px-12 py-12 grid-cols-2 grid gap-8 items-center overflow-hidden'>
      <div className="absolute inset-0 z-0">
        <Aurora
          colorStops={["#8363f2", "#f2d231", "#a5a5a5"]}
          blend={0.5}
          amplitude={1.0}
          speed={1}
        />
      </div>

      {/* Contenido de "Registra tu cuenta" */}
      <div className="relative z-10">
        <h2 className="text-3xl font-bold mb-4 text-white relative">
          Registra tu <span className="relative z-10">Cuenta </span>
          <span className="absolute inset-0 w-20 h-2 bg-primary top-6 left-48 z-0"></span>
          GRATIS para<br />
          acceder a <span className="text-secondary">300</span> cursos online
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <img src={logo} alt="logo" className="w-12 h-auto" />
          <p>
            Aprende a manejar Python con Inteligencia Artificial en un solo paso.
          </p>
        </div>
      </div>

        {/* Formulario */}
        <div className="relative z-10 text-black p-6 rounded-lg shadow-md bg-dark">
          <form>
            <div className="mb-4">
              <label className="block text-white font-bold text-2xl mb-4">
                Completa tu Registro
              </label>
              <label className="block text-white text-sm font-medium mb-1">
                Tu Nombre Completo
              </label>
              <input
                type="text"
                className="w-full border rounded-md p-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
                placeholder="Ingresa tu nombre completo"
              />
            </div>
            <div className="mb-4">
              <label className="block text-white text-sm font-medium mb-1">
                Teléfono
              </label>
              <input
                type="text"
                className="w-full border rounded-md p-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
                placeholder="Ingresa tu teléfono"
              />
            </div>
            <div className="mb-4">
              <label className="block text-white text-sm font-medium mb-1">
                Correo Electrónico
              </label>
              <input
                type="email"
                className="w-full border rounded-md p-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
                placeholder="xxxxx@gmail.com"
              />
            </div>
            <div className="mb-4">
              <label className="block text-white text-sm font-medium mb-1">
                Contraseña
              </label>
              <input
                type="password"
                className="w-full border rounded-md p-2 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
                placeholder="●●●●●●●●"
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
        </div>
        </FadeContent>
      </section>




      {/* Footer */}
      <footer className="bg-dark py-6 text-center text-white font-semibold">
        <p>© 2025 Pycher. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}
