import { useEffect, useState } from "react";
import { useParams, Link } from "@tanstack/react-router";
import { getCourseById, getModulesByCourseId } from "@/services/contentService";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { BookOpen, Clock, Users, Star } from "lucide-react";
import { ModuleCard } from "@/components/courses/ModuleCard";
import { courseDetailRoute } from "@/router";
import AnimatedContent from '../../components/ui/animated-content';
import SplitText from "../../components/ui/split-text";

export default function CourseDetailPage() {
  const { courseId } = useParams({ from: courseDetailRoute.id });
  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);

  const handleAnimationComplete = () => {
  console.log('All letters have animated!');
};

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
      <div className="bg-gradient-to-r from-[#312a56] to-[#1a1433] rounded-lg p-8 mb-8 shadow-lg m-6">
        <h2 className="text-4xl font-bold text-white mb-2">{course.title}</h2>
        <p className="text-gray-300 mb-4 text-lg">{course.description}</p>
        <div className="flex flex-wrap gap-6 mb-4">
          <div className="flex items-center gap-2 text-gray-300">
            <BookOpen className="w-5 h-5 text-[#5f2dee]" />
            <span>{course.total_modules} módulos</span>
          </div>
          <div className="flex items-center gap-2 text-gray-300">
            <Clock className="w-5 h-5 text-[#5f2dee]" />
            <span>{course.duration_minutes} min</span>
          </div>
          <div className="flex items-center gap-2 text-gray-300">
            <Users className="w-5 h-5 text-[#5f2dee]" />
            <span>{course.students_count} estudiantes</span>
          </div>
          <div className="flex items-center gap-2 text-gray-300">
            <Star className="w-5 h-5 text-[#f2d231]" fill="#f2d231" />
            <span>{course.rating}</span>
          </div>
        </div>
        <div className="flex gap-4 mt-4">
          <Link
            to="/courses"
            className="bg-primary hover:bg-primary-opaque text-white px-4 py-2 rounded-md"
          >
            Volver a Cursos
          </Link>
        </div>
      </div>
      </AnimatedContent>

      <SplitText
        text="Cursos disponibles para ti"
        className="text-2xl font-bold text-white mx-6 mb-4"
        delay={20}
        animationFrom={{ opacity: 0, transform: 'translate3d(0,0,0)' }}
        animationTo={{ opacity: 1, transform: 'translate3d(0,0,0)' }}
        easing="easeInOutCubic"
        threshold={0}
        rootMargin="-100px"
        onLetterAnimationComplete={handleAnimationComplete}
      />

      {modules.length === 0 ? (
        <div className="text-gray-400 mx-6 mt-6">Este curso aún no tiene módulos.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mx-6">
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
