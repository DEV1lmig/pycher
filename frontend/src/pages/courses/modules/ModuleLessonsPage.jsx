import { useEffect, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { getModuleById, getLessonsByModuleId } from "@/services/contentService";
import { moduleLessonsRoute } from "@/router";
import DashboardLayout from "@/components/dashboard/DashboardLayout";

export default function ModuleLessonsPage() {
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

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-white">
          Cargando módulo...
        </div>
      </DashboardLayout>
    );
  }
  if (!module) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-red-400">
          Módulo no encontrado
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="bg-primary/20 rounded-lg p-8 mb-8 shadow-lg m-6">
        <h1 className="text-3xl font-bold text-white mb-2">{module.title}</h1>
        <p className="text-gray-300 mb-4">{module.description}</p>
        <Link
          to={`/courses/${courseId}`}
          className="inline-block bg-primary hover:bg-primary-opaque text-white px-4 py-2 rounded-md mt-2"
        >
          Volver al curso
        </Link>
      </div>
      <h2 className="text-2xl font-bold text-white mb-4 mx-6">Lecciones del módulo</h2>
      <div className="space-y-4">
        {lessons.length === 0 ? (
          <div className="text-gray-400 mx-6">Este módulo no tiene lecciones.</div>
        ) : (
          lessons.map(lesson => (
            <Link
              key={lesson.id}
              to={`/lessons/${lesson.id}`}
              className="block overflow-hidden border m-6 cursor-default transition-transform duration-300 ease-out 
              hover:scale-105 border-dark-light hover:border-primary h-full rounded-2xl flex flex-col"
            >
              <div className="font-semibold text-xl text-primary font-bold m-6">{lesson.title}</div>
              <div className="text-white mx-6 mb-6 mt-4">{lesson.content?.slice(0, 80)}...</div>
            </Link>
          ))
        )}
      </div>
    </DashboardLayout>
  );
}
