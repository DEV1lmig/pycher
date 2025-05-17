import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { getModuleById, getLessonsByModuleId } from "@/services/contentService";
import { moduleLessonsRoute } from "@/router";
import { MainLayout } from "@/components/layout/MainLayout";
import FadeContent from '../../../components/ui/fade-content.jsx';

export default function ModuleLessonsPage() {
  // Use useParams with the route context to get moduleId
  const { moduleId, courseId } = useParams({ from: moduleLessonsRoute.id });
  const [module, setModule] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getModuleById(moduleId),
      getLessonsByModuleId(moduleId)
    ]).then(([mod, lessons]) => {
      setModule(mod);
      setLessons(lessons);
    }).finally(() => setLoading(false));
  }, [moduleId]);

  if (loading) return <MainLayout><div className="p-8 text-center">Cargando módulo...</div></MainLayout>;
  if (!module) return <MainLayout><div className="p-8 text-center text-red-600">Módulo no encontrado</div></MainLayout>;

  return (
    <MainLayout>
      <FadeContent blur={true} duration={1000} easing="ease-out" initialOpacity={0}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{module.title}</h1>
        <p className="text-gray-400 mb-4">{module.description}</p>
      </div>
      <div className="space-y-4">
        {lessons.length === 0 ? (
          <div className="text-gray-500">Este módulo no tiene lecciones.</div>
        ) : (
          lessons.map(lesson => (
            <Link
              key={lesson.id}
              to={`/courses/${courseId}/lessons/${lesson.id}`}
              className="block bg-white/80 rounded-lg shadow p-4 hover:bg-primary/10 transition"
            >
              <div className="font-semibold text-lg">{lesson.title}</div>
              <div className="text-gray-500">{lesson.content?.slice(0, 80)}...</div>
            </Link>
          ))
        )}
      </div>
      </FadeContent>
    </MainLayout>
  );
}
