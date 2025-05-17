import { useState, useEffect } from "react";
import { useParams } from "@tanstack/react-router";
import { MainLayout } from "@/components/layout/MainLayout";
import { CodeEditor } from "@/components/editor/CodeEditor";
import { getCodeHint } from "@/services/aiService";
import { executeCode } from "@/services/executionService";
import { Button } from "@/components/ui/button";
import { LessonsWithCodeRoute } from "@/router";

export default function LessonWithCodePage() {
  const { lessonId } = useParams({ from: LessonsWithCodeRoute.id });
  const [lesson, setLesson] = useState(null);
  const [loadingLesson, setLoadingLesson] = useState(true);
  const [lessonError, setLessonError] = useState(null);

  const [code, setCode] = useState("");
  const [output, setOutput] = useState("");
  const [execLoading, setExecLoading] = useState(false);

  const [aiHelp, setAiHelp] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  // Fetch lesson data
  useEffect(() => {
    setLoadingLesson(true);
    setLessonError(null);
    fetch(`/api/v1/content/lessons/${lessonId}`)
      .then(res => {
        if (!res.ok) throw new Error("Lesson not found");
        return res.json();
      })
      .then(data => {
        setLesson(data);
        setCode(data.starterCode || "");
      })
      .catch(err => setLessonError(err.message))
      .finally(() => setLoadingLesson(false));
  }, [lessonId]);

  // Handle code execution
  const handleExecute = async () => {
    setExecLoading(true);
    setOutput("");
    try {
      const result = await executeCode({ code, language: "python" });
      setOutput(result.output || result.error || "No output.");
    } catch (err) {
      setOutput("Execution failed.");
    }
    setExecLoading(false);
  };

  // Handle AI help
  const handleAiHelp = async () => {
    setAiLoading(true);
    setAiHelp("");
    try {
      const result = await getCodeHint({
        code,
        instruction: lesson?.instruction || lesson?.title || "Give a hint for this code."
      });
      setAiHelp(result.content || "No suggestion available.");
    } catch (err) {
      setAiHelp("Unable to get AI help at this time.");
    }
    setAiLoading(false);
  };

  if (loadingLesson) {
    return <MainLayout><div className="p-8 text-center">Loading lesson...</div></MainLayout>;
  }
  if (lessonError) {
    return <MainLayout><div className="p-8 text-center text-red-600">{lessonError}</div></MainLayout>;
  }

  return (
    <MainLayout>
      <div className="flex flex-col md:flex-row gap-6">
        {/* Lesson Section */}
        <section className="md:w-1/2 bg-white/80 rounded-lg shadow p-6 prose max-w-none">
          <h2 className="font-bold text-xl mb-2">{lesson.title}</h2>
          <div dangerouslySetInnerHTML={{ __html: lesson.body.replace(/\n/g, "<br/>") }} />
        </section>

        {/* Code Editor Section */}
        <section className="md:w-1/2 flex flex-col gap-4">
          <CodeEditor
            initialCode={code}
            onChange={setCode}
            onExecute={handleExecute}
          />
          <div className="flex gap-2">
            <Button onClick={handleExecute} disabled={execLoading}>
              {execLoading ? "Running..." : "Run Code"}
            </Button>
            <Button onClick={handleAiHelp} disabled={aiLoading}>
              {aiLoading ? "Getting AI Help..." : "Get AI Help"}
            </Button>
          </div>
          {output && (
            <div className="bg-gray-900 text-green-200 rounded p-3 mt-2 font-mono text-sm">
              <strong>Output:</strong>
              <pre className="whitespace-pre-wrap">{output}</pre>
            </div>
          )}
          {aiHelp && (
            <div className="bg-blue-50 border border-blue-200 rounded p-3 mt-2 text-blue-900">
              <strong>AI Suggestion:</strong>
              <div className="mt-1 whitespace-pre-line">{aiHelp}</div>
            </div>
          )}
        </section>
      </div>
    </MainLayout>
  );
}
