import { useEffect, useState } from "react";
import { useParams } from "@tanstack/react-router";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { getLessonById } from "@/services/contentService";
import { CodeEditor } from "@/components/editor/CodeEditor";
import { Button } from "@/components/ui/button";
import { LessonWithCodeRoute } from "@/router";

export default function LessonWithCodePage() {
  const { lessonId } = useParams({ from: LessonWithCodeRoute.id });
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lessonError, setLessonError] = useState(null);
  console.log("LessonWithCodePage - lessonId:", lessonId);
  const [code, setCode] = useState("");
  const [output, setOutput] = useState("");
  const [execLoading, setExecLoading] = useState(false);

  useEffect(() => {
    console.log("LessonWithCodePage - lessonId:", lessonId);
    setLoading(true);
    setLessonError(null);
    getLessonById(lessonId)
      .then(data => {
        console.log("Lesson data from backend:", data);
        setLesson(data);
      })
      .catch(err => setLessonError(err.message))
      .finally(() => setLoading(false));
  }, [lessonId]);

  const handleExecute = async () => {
    setExecLoading(true);
    setOutput("");
    try {
      // Replace with your actual code execution logic
      // const result = await executeCode(code);
      // setOutput(result.output || result.error || "No output.");
      setOutput("Código ejecutado (simulado).");
    } catch (err) {
      setOutput("Execution failed.");
    }
    setExecLoading(false);
  };

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
        <p className="text-gray-300 mb-4">{lesson.description || ""}</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Lesson Content Card */}
        <div className="bg-[#1a1433] rounded-lg shadow border border-[#312a56] p-6 flex flex-col">
          <h2 className="font-bold text-xl text-white mb-2">{lesson.title}</h2>
          <div className="prose max-w-none text-gray-200 whitespace-pre-line">
            {lesson.content}
          </div>
        </div>
        {/* Code Editor Card */}
        <div className="bg-[#1a1433] rounded-lg shadow border border-[#312a56] p-6 flex flex-col gap-4">
          <div className="font-semibold text-lg text-white mb-2">Editor de Código</div>
          <CodeEditor
            initialCode={code}
            onChange={setCode}
            onExecute={handleExecute}
          />
          <div className="flex gap-2 mt-2">
            <Button onClick={handleExecute} disabled={execLoading} className="bg-[#5f2dee] hover:bg-[#4f25c5] text-white">
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
    </DashboardLayout>
  );
}
