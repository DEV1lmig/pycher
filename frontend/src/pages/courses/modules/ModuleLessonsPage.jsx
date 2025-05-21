import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { getCourseById, getModuleById, getLessonsByModuleId } from "@/services/contentService";
import { moduleLessonsRoute } from "@/router";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import Waves from "@/components/ui/waves";
import FadeContent from "@/components/ui/fade-content";
import AnimatedContent from "@/components/ui/animated-content";
import { BookOpen, Home } from "lucide-react";
import Breadcrumbs from "@/components/ui/breadcrumbs";

export default function ModuleLessonsPage() {
  const { moduleId, courseId } = useParams({ from: moduleLessonsRoute.id });
  const [course, setCourse] = useState(null);
  const [module, setModule] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
  setLoading(true);
  getModuleById(moduleId)
    .then((mod) => {
      setModule(mod);
      return getCourseById(mod.course_id).then((course) => {
        setCourse(course);
      });
    })
    .then(() => getLessonsByModuleId(moduleId).then((lessons) => {
      setLessons(Array.isArray(lessons) ? lessons : []);
    }))
    .finally(() => setLoading(false));
}, [moduleId]);

  if (loading || !course || !module) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-white">
          Cargando módulo...
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
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
      <div className="my-4 mx-6">
        <Breadcrumbs
        items={[
          { label: "Inicio", href: "/home", icon: <Home size={16} /> },
          { label: "Cursos", href: "/courses", icon: <BookOpen size={16} /> },
          { label: course.title, href: `/courses/${course.id}` },
          { label: module.title },
        ].filter(Boolean)}
      />
      
      </div>
      <div className="relative rounded-lg p-8 mb-8 shadow-2xl m-6">
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
        xGap={5}
        yGap={36}
      />
      </div>
      <div className="relative z-20">
        <h1 className="text-3xl font-bold text-white mb-2">{module.title}</h1>
        <p className="text-gray-300 mb-4">{module.description}</p>
        <Link
        to={`/courses/${course?.id}`}
        className="inline-block bg-secondary hover:bg-secondary/90 text-dark font-semibold px-4 py-2 rounded-md mt-2"
      >
        Volver al curso
      </Link>
      </div>
      </div>
      </AnimatedContent>
        
      <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100}>
      <h2 className="text-2xl font-bold text-white mb-4 mx-6">Lecciones del módulo</h2>
      <div
        className="mx-6 bg-dark-light/10 rounded-lg p-4 custom-scroll"
        style={{ maxHeight: "400px", overflowY: "auto" }} 
      >
        {lessons.length === 0 ? (
          <div className="text-gray-400">Este módulo no tiene lecciones.</div>
        ) : (
          lessons.map(lesson => (
            <Link
              key={lesson.id}
              to={`/lessons/${lesson.id}`}
              className="block bg-primary-opaque/10 rounded-lg border hover:bg-dark hover:scale-101 
              border-primary-opaque/0 hover:border-primary transition-all ease-out duration-300 cursor-default 
              shadow-lg mb-4"
            >
              <div className="font-semibold hover:text-secondary text-xl text-white font-bold p-6">
                {lesson.title}
                <p className="text-gray-400 text-base mt-4">{lesson.content?.slice(0, 80)}...</p>
              </div>
            </Link>
          ))
        )}
      </div>
    </FadeContent>
    </DashboardLayout>
  );

  
}
