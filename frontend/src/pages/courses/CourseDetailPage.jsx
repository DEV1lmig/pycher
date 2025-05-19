import { useEffect, useState } from "react";
import { useParams, Link } from "@tanstack/react-router";
import { getCourseById, getModulesByCourseId } from "@/services/contentService";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { BookOpen, Clock, Users, Star } from "lucide-react";
import { ModuleCard } from "@/components/courses/ModuleCard";
import { courseDetailRoute } from "@/router";
import AnimatedContent from '../../components/ui/animated-content';
import  FadeContent from "@/components/ui/fade-content";
import Waves from "@/components/ui/waves";

export default function CourseDetailPage() {
  const { courseId } = useParams({ from: courseDetailRoute.id });
  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);

  useEffect(() => {
    getCourseById(courseId).then(setCourse);
  }, [courseId]);

  useEffect(() => {
    if (!courseId) return;
    getModulesByCourseId(courseId)
      .then(data => {
        // Always normalize to array
        if (Array.isArray(data)) setModules(data);
        else if (data) setModules([data]);
        else setModules([]);
      })
      .catch(() => setModules([]));
  }, [courseId]);

  if (!course) return <div className="text-white">Cargando...</div>;

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
      <div className="bg-dark rounded-3xl relative p-8 mb-8 shadow-3xl border-primary/5 border m-6">
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
        <h2 className="text-4xl font-bold text-white mb-2">{course.title}</h2>
        <p className="text-white mb-4 text-lg">{course.description}</p>
        <div className="flex  flex-wrap gap-6 mb-4">
          <div className="flex items-center gap-2 text-white">
            <BookOpen className="w-5 h-5 text-primary" />
            <span>{course.total_modules} módulos</span>
          </div>
          <div className="flex items-center gap-2 text-white">
            <Clock className="w-5 h-5 text-primary" />
            <span>{course.duration_minutes} min</span>
          </div>
          <div className="flex items-center gap-2 text-white">
            <Users className="w-5 h-5 text-primary" />
            <span>{course.students_count} estudiantes</span>
          </div>
          <div className="flex items-center gap-2 text-white">
            <Star className="w-5 h-5 text-[#f2d231]" fill="#f2d231" />
            <span>{course.rating}</span>
          </div>
        </div>
        <div className="flex gap-4 mt-4">
          <Link
            to="/courses"
            className="bg-secondary hover:bg-secondary/80 text-dark font-semibold px-4 py-2 rounded-md"
          >
            Volver a Cursos
          </Link>
        </div>
      </div>
        
      </div>
      </AnimatedContent>

      <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100} >
      <h3 className="text-2xl font-bold text-white mx-6">Cursos disponibles para ti</h3>
      </FadeContent>

      {modules.length === 0 ? (
        <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100} >
        <div className="flex justify-center p-32 text-gray-400 mx-6 mt-6">¡Oh no!, este curso aún no cuenta con módulos :( </div></FadeContent>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mx-6 items-stretch">
          {modules.map((module) => (
            <ModuleCard key={module.id} module={module}>
              <Link
                to={`/courses/${course.id}/modules/${module.id}`}
                className="bg-primary text-white px-4 py-2 rounded  hover:bg-primary-dark"
              >
                Ver lecciones
              </Link>
            </ModuleCard>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}
