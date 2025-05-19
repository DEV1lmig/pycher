import DashboardLayout from "@/components/dashboard/DashboardLayout"
import Accordion from "../../components/ui/accordion";
import  Iridescence  from "../../components/ui/iridescence";
import FadeContent from "../../components/ui/fade-content.jsx";
import AnimatedContent from "../../components/ui/animated-content.jsx";

export default function HelpPage() {
  const faqItems = [
    {
      title: "¿Cómo me registro?",
      subtitle: "Registro rápido y sencillo",
      content: "Haz clic en 'Registrarse', completa el formulario y listo.",
    },
    {
      title: "Olvidé mi contraseña",
      subtitle: "Recuperación de contraseña",
      content: "Utiliza la opción '¿Olvidaste tu contraseña?' en la pantalla de inicio de sesión.",
    },
    {
      title: "¿Puedo acceder a los cursos gratis?",
      subtitle: "Cursos gratuitos",
      content: "Sí, todos los cursos son gratuitos.",
    },
    {
      title: "¿Puedo ver el curso Avanzado sin ver el Básico?",
      subtitle: "Cursos secuenciales",
      content: "No, lamentamos que no está permitido. Debes ver el curso Básico primero.",
    },
    {
      title: "¿Debo tener algún conocimiento básico de programación?",
      subtitle: "Conocimientos previos",
      content: "Si, se recomienda tener conocimientos básicos de programación. Sin embargo, el curso está diseñado para principiantes.",
    },
    {
      title: "¿Esta página sirve de material de apoyo para mis clases de programación?",
      subtitle: "Material de apoyo",
      content: "Sí, absolutamente. Puedes usarla como material de apoyo para tus clases.",
    },
  ];


  return (
    <DashboardLayout>
      <div className="flex flex-col">
      <section>
        <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={1}>
        <div className="flex items-center justify-center my-10 gap-4">
            <div className="relative w-full max-w-2xl h-44 flex items-center justify-center rounded-3xl overflow-hidden">
            <Iridescence
                color={[0.5, 0.4, 1]}
                mouseReact={false}
                amplitude={0.1}
                speed={1.0}
                className="absolute inset-0 w-full h-full z-0"
            />
            <h2 className="relative z-10 opacity-60 text-4xl font-bold text-center px-2 mix-blend-lighten"
            >Preguntas Frecuentes</h2>
            </div>
        </div>
        </FadeContent>

        <AnimatedContent
          distance={100}
          direction="vertical"
          reverse={false}
          config={{ tension: 90, friction: 20 }}
          initialOpacity={0}
          animateOpacity
          scale={1}
          threshold={0.2}
          delay={100}
        >
        <Accordion items={faqItems} /></AnimatedContent>
        </section>
    </div>
    </DashboardLayout>
  )
}
