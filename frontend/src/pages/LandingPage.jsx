import React, {useState, useEffect} from 'react';
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
import FaqCarousel from "../components/ui/carousel";

export default function LandingPage() {
  const [showScrollIndicator, setShowScrollIndicator] = useState(true);
  const [isTitleAnimationComplete, setIsTitleAnimationComplete] = useState(false); // 1. Add new state

  const Items = [
    { title: "Increíble experiencia", content: "Perfecto para empezar. Cubre Python básico y aplicaciones simples de IA. Ejercicios útiles y claros." },
    { title: "Curso rápido y directo", content: "Enseña algoritmos esenciales (regresión, clasificación) con proyectos reales. Ideal para quienes tienen prisa." },
      { title: "Conocimiento de Programación", content: "No se requiere de conocimiento de programación para empezar, una maravilla!" },
    { title: "Aprender Python", content: "Para aquellas personas que les interesa aprender Python, échenle un ojo a esto!" },

  ];

  // 2. Define the handler to update the state
  const handleAnimationComplete = () => {
    setIsTitleAnimationComplete(true);
  };

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 0) {
        setShowScrollIndicator(false);
      } else {
        setShowScrollIndicator(true);
      }
    };

    window.addEventListener('scroll', handleScroll);

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
  <div className="relative group min-h-screen bg-dark text-white ">
    <NavBar />
    <div className="relative group overflow-hidden pt-60 pb-48">
      <div className="absolute inset-0 bg-dark">
      </div>
       <div className="absolute top-2/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10 mt-[4rem]">
        <AnimatedContent
          distance={100}
          direction="vertical"
          reverse={false}
          config={{ tension: 60, friction: 40 }}
          initialOpacity={0.2}
          animateOpacity
          scale={0.5}
          threshold={0.2}
        >
          <div className="text-8xl md:text-[250px] font-bold text-white cursor-default">
            pycher
            <span className="text-primary">.</span>
          </div>

        </AnimatedContent>
    </div>

      {showScrollIndicator && (
    <div className="fixed bottom-10 left-1/2 transform -translate-x-1/2 w-[2px] bg-primary rounded-full animate-scroll-line"></div>
  )}

    <header className="relative container mx-auto px-4 pt-36 text-center min-h-[500px] overflow-visible">
      <AnimatedContent
        distance={100}
        direction="vertical"
        reverse={true}
        config={{ tension: 60, friction: 40 }}
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
          <div className="relative z-10 w-[250px] h-[250px] md:w-[200px] md:h-[200px] bg-dark overflow-hidden border-[5px] border-solid border-tertiary rounded-[30px] transition-all duration-300 ease-in-out hover:scale-95">
            <div className="absolute inset-0 transition-opacity cursor-pointer duration-300 ease-in-out hover:opacity-10">
              <Waves
                lineColor="#a5a5a5"
                backgroundColor="#160f30"
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
            <Magnet padding={30} disabled={false} magnetStrength={0.8}>
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
          <div className="relative z-10 w-[250px] h-[250px] md:w-[200px] md:h-[200px] bg-dark overflow-hidden border-[5px] border-solid border-secondary rounded-full transition-all duration-300 ease-in-out hover:scale-95">
            <div className="absolute inset-0 transition-opacity duration-300 ease-in-out hover:opacity-10">
              <Squares
                speed={0.1}
                squareSize={30}
                direction="right"
                borderColor="#f2d231"
                hoverFillColor="#222"
              />
            </div>
          </div>
        </div>
      </AnimatedContent>

      <div className="font-normal text-2xl flex justify-between items-center mt-12 px-36">

      <FadeContent blur={true} duration={1600} easing="ease-out" initialOpacity={0}>
        <div className="flex flex-col text-left">
          <p>Obtén guía personalizada</p>
          <p>Y feedback en <span className="text-primary">tiempo real</span></p>
        </div>
      </FadeContent>
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

      {/* 3. Conditionally render the cards based on the state */}
      {isTitleAnimationComplete && [...Array(3)].map((_, index) => (
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
            imageHeight="270px"
            imageWidth="270px"
            rotateAmplitude={12}
            scaleOnHover={1.2}
            showMobileWarning={false}
            showTooltip={false}
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

      {/* --- STATISTICS SECTION SIMPLIFIED --- */}
      <section className="bg-dark py-24 flex justify-center items-center gap-12">
      <FadeContent blur={true} duration={1200} easing="ease-out" initialOpacity={0}>
      <div className="relative w-[465px] h-[250px] bg-primary overflow-hidden border-none rounded-2xl ">
          <div className="absolute inset-0">
            <Squares
              speed={0.3}
              squareSize={30}
              direction="down"
              borderColor="#9880f2"
              hoverFillColor="#222"
            />
          </div>

          <div className="relative z-10 flex flex-col items-start justify-end h-full ml-7">
            <div className="flex items-center text-dark text-9xl font-bold">
              <CountUp
                from={0}
                to={3}
                separator=""
                direction="up"
                duration={1}
                className="count-up-text"
              />
              <span className="text-dark">+</span>
            </div>
            <div className="text-dark text-2xl font-bold mb-5">
              Cursos Interactivos
            </div>
          </div>
      </div>
      </FadeContent>

      {/* The "Certificados" card has been removed as requested. */}
      </section>
      {/* --- END OF SIMPLIFICATION --- */}


      <FadeContent blur={true} duration={1600} easing="ease-out" initialOpacity={0}>
      <section className='bg-dark'>
        <div className="flex flex-col items-center justify-center mt-12 ">
            <h1 className="text-4xl font-bold text-white">Esto es lo que dicen nuestros usuarios</h1>
            <p className="mt-3 text-lg text-secondary">Ellos piensan que nuestros cursos son increíbles, tú también puedes pensarlo!</p>
        </div>
        <div className="relative w-full max-w-7xl mx-auto py-8">
        {/* Fade left */}
        <div className="pointer-events-none absolute left-0 top-0 h-full w-24 z-20"
            style={{
                background: "linear-gradient(to right, #160f30 60%, transparent 100%)"
            }}
        />
        {/* Fade right */}
        <div className="pointer-events-none absolute right-0 top-0 h-full w-24 z-20"
            style={{
                background: "linear-gradient(to left, #160f30 60%, transparent 100%)"
            }}
        />
        <FaqCarousel items={Items} />
        </div>
        </section>
        </FadeContent>

      {/* Footer */}
      <footer className="bg-dark-background py-6 text-center text-white font-semibold">
        <p>© 2025 Pycher. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}
