import { useEffect, useState } from "react";
import { useParams } from "@tanstack/react-router";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { getLessonById, getExercisesByLessonId } from "@/services/contentService";
import { LessonWithCodeRoute } from "@/router";
import LessonCodeExecutor from "@/components/editor/LessonCodeExecutor";

export default function LessonWithCodePage() {
  const { lessonId } = useParams({ from: LessonWithCodeRoute.id });
  const [lesson, setLesson] = useState(null);
  const [exercise, setExercise] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lessonError, setLessonError] = useState(null);
  const [initialCode, setInitialCode] = useState("");

  useEffect(() => {
    setLoading(true);
    setLessonError(null);
    Promise.all([
      getLessonById(lessonId),
      getExercisesByLessonId(lessonId)
    ])
      .then(([lessonData, exercises]) => {
        setLesson(lessonData);
        if (exercises && exercises.length > 0) {
          setExercise(exercises[0]);
          setInitialCode(exercises[0].starter_code || "");
        } else {
          setExercise(null);
          setInitialCode("");
        }
      })
      .catch(err => setLessonError(err.message))
      .finally(() => setLoading(false));
  }, [lessonId]);

  if (loading) {
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
      <div className="bg-gradient-to-r from-[#312a56] to-[#1a1433] rounded-lg p-8 mb-8 shadow-lg border border-[#312a56]">
        <h1 className="text-3xl font-bold text-white mb-2">{lesson.title}</h1>
      </div>
      {exercise && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left: Lesson Content & Exercise Description */}
          <div className="bg-[#1a1433] rounded-lg shadow border border-[#312a56] p-6 flex flex-col">
            <div className="text-gray-300 mb-4 whitespace-pre-line">{lesson.content}</div>
            <h2 className="font-semibold text-xl text-white mb-2 mt-4">{exercise.title}</h2>
            <div className="text-gray-300">{exercise.description}</div>
          </div>
          {/* Right: Code Editor & Output */}
          <div className="bg-[#1a1433] rounded-lg shadow border border-[#312a56] p-6 flex flex-col gap-4">
            <LessonCodeExecutor initialCode={initialCode} />
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
