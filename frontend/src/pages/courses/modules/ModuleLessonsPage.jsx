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
      <div className="bg-gradient-to-r from-[#312a56] to-[#1a1433] rounded-lg p-8 mb-8 shadow-lg">
        <h1 className="text-3xl font-bold text-white mb-2">{module.title}</h1>
        <p className="text-gray-300 mb-4">{module.description}</p>
        <Link
          to={`/courses/${courseId}`}
          className="inline-block bg-[#5f2dee] hover:bg-[#4f25c5] text-white px-4 py-2 rounded-md mt-2"
        >
          Volver al curso
        </Link>
      </div>
      <h2 className="text-2xl font-bold text-white mb-4">Lecciones del módulo</h2>
      <div className="space-y-4">
        {lessons.length === 0 ? (
          <div className="text-gray-400">Este módulo no tiene lecciones.</div>
        ) : (
          lessons.map(lesson => (
            <Link
              key={lesson.id}
              to={`/lessons/${lesson.id}`}
              className="block bg-white/80 rounded-lg shadow p-4 hover:bg-primary/10 transition"
            >
              <div className="font-semibold text-lg text-[#312a56]">{lesson.title}</div>
              <div className="text-gray-600">{lesson.content?.slice(0, 80)}...</div>
            </Link>
          ))
        )}
      </div>
    </DashboardLayout>
  );
}
