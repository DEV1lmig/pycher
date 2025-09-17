import { useState } from "react";
import DashboardLayout from "@/components/dashboard/DashboardLayout"
import Accordion from "../../components/ui/accordion";
import FadeContent from "../../components/ui/fade-content.jsx";
import AnimatedContent from "../../components/ui/animated-content.jsx";
import Waves from "@/components/ui/waves";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { downloadUserManualWithNotification } from "@/services/contentService";
import { useDownloadNotification } from "@/hooks/useDownloadNotification";

export default function HelpPage() {
  const [isDownloading, setIsDownloading] = useState(false);
  const downloadNotification = useDownloadNotification();

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      await downloadUserManualWithNotification("manual_de_usuario_pycher.pdf", downloadNotification);
    } catch (error) {
      // Error handling is now managed by the downloadUserManualWithNotification function
      // through the notification system, so we don't need to handle it here
      console.error("Download error:", error);
    } finally {
      setIsDownloading(false);
    }
  };

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
        <div className="bg-dark rounded-3xl relative p-8 mb-8 shadow-3xl border-primary/5 border h-32">
            <div className="absolute inset-0 z-10">
              <Waves
              lineColor="rgba(152, 128, 242, 0.4)"
              backgroundColor="#160f30"
              waveSpeedX={0.02}
              waveSpeedY={0.01}
              waveAmpX={70}
              waveAmpY={20}
              friction={0.9}
              tension={0.01}
              maxCursorMove={60}
              xGap={12}
              yGap={36}
            />
            </div>
            <div className="relative z-20 flex flex-col items-center">
              <h2 className="relative z-10 text-4xl font-bold text-center px-2 mix-blend-lighten">
                Preguntas Frecuentes
              </h2>
              <Button
                onClick={handleDownload}
                disabled={isDownloading}
                className="mt-4 bg-primary hover:bg-primary/80 text-white font-semibold"
              >
                <Download className="mr-2 h-4 w-4" />
                {isDownloading ? "Descargando..." : "Descargar Manual de Usuario"}
              </Button>
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
