import { useEffect, useState } from "react";
import { useParams, Link } from "@tanstack/react-router";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { getLessonById, getModuleById, getCourseById } from "@/services/contentService";
import { CodeEditor } from "@/components/editor/CodeEditor";
import { Button } from "@/components/ui/button";
import { LessonWithCodeRoute } from "@/router";
import Waves from "@/components/ui/waves";
import AnimatedContent from "@/components/ui/animated-content";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen } from "lucide-react";

export default function LessonWithCodePage() {
  const { lessonId } = useParams({ from: LessonWithCodeRoute.id });
  const [lesson, setLesson] = useState(null);
  const [module, setModule] = useState(null);
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lessonError, setLessonError] = useState(null);
  const [code, setCode] = useState("");
  const [output, setOutput] = useState("");
  const [execLoading, setExecLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    setLessonError(null);
    getLessonById(lessonId)
      .then(data => {
        setLesson(data);
        // Cargar módulo y curso relacionados
        return getModuleById(data.module_id).then(mod => {
          setModule(mod);
          return getCourseById(mod.course_id).then(course => {
            setCourse(course);
          });
        });
      })
      .catch(err => setLessonError(err.message))
      .finally(() => setLoading(false));
  }, [lessonId]);

  const handleExecute = async () => {
    setExecLoading(true);
    setOutput("");
    try {
      setOutput("Código ejecutado (simulado).");
    } catch (err) {
      setOutput("Execution failed.");
    }
    setExecLoading(false);
  };

  if (loading || !lesson || !module || !course) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-white">
          Cargando lección...
        </div>
      </DashboardLayout>
    );
  }

  if (lessonError) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-red-400">
          {lessonError}
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="my-4 mx-6">
        <Breadcrumbs
          items={[
            { label: "Inicio", href: "/home", icon: <Home size={16} /> },
            { label: "Cursos", href: "/courses", icon: <BookOpen size={16} /> },
            { label: course.title, href: `/courses/${course.id}` },
            { label: module.title, href: `/module/${module.id}` },
            { label: lesson.title },
          ].filter(Boolean)}
        />
      </div>
      <AnimatedContent
        distance={40}
        direction="vertical"
        reverse={true}
        config={{ tension: 100, friction: 20 }}
        initialOpacity={0.2}
        animateOpacity
        scale={1}
        threshold={0.2}
      >
        <div className="relative rounded-lg p-8 mx-6 my-6 shadow-2xl border border-primary-opaque/0">
          <div className="absolute rounded-3xl overflow-hidden inset-0 z-10">
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
          <div className="relative z-20">
            <h1 className="text-3xl font-bold text-white mb-2">{lesson.title}</h1>
            <p className="text-gray-400 mb-4">{lesson.description || ""}</p>
          </div>
        </div>
      </AnimatedContent>

      <FadeContent blur={true} duration={300} easing="ease-out" initialOpacity={0} delay={100} >
        <div className="grid grid-cols-1 md:grid-cols-2 mx-6 gap-6">
          {/* Lesson Content Card */}
          <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow p-6 flex flex-col">
            <h2 className="font-bold text-xl text-secondary mb-2">{lesson.title}</h2>
            <hr className="mb-4 border-primary/40" />
            <div className="prose text-justify max-w-none text-gray-200 whitespace-pre-line">
              {lesson.content}
            </div>
          </div>
          {/* Code Editor Card */}
          <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow p-6 flex flex-col gap-4">
            <div className="font-semibold text-lg text-secondary mb-2">Editor de Código</div>
            <CodeEditor
              initialCode={code}
              onChange={setCode}
              onExecute={handleExecute}
            />
            <div className="flex gap-2 mt-2">
              <Button onClick={handleExecute} disabled={execLoading} className="bg-primary hover:bg-primary-opaque text-white">
                {execLoading ? "Ejecutando..." : "Ejecutar Código"}
              </Button>
            </div>
            {output && (
              <div className="bg-gray-900 text-green-200 rounded p-3 mt-2 font-mono text-sm border border-gray-700">
                <strong>Salida:</strong>
                <pre className="whitespace-pre-wrap">{output}</pre>
              </div>
            )}
          </div>
        </div>
      </FadeContent>
    </DashboardLayout>
  );
}