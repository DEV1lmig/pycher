import { useState } from "react";
import { CodeEditor } from "./CodeEditor";
import { Button } from "../ui/button";
import { OutputDisplay } from "@/components/editor/OutputDisplay";
import { getCodeHint } from "@/services/aiService";

export default function LessonCodeExecutor({
  initialCode = "",
  onSubmitCode,
  isCorrect,
  // The 'currentUserStdin' prop is no longer used and has been removed.
}) {
  const [tab, setTab] = useState("editor");
  const [code, setCode] = useState(initialCode);
  const [output, setOutput] = useState("");
  const [error, setError] = useState("");
  const [passed, setPassed] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingHint, setIsLoadingHint] = useState(false);
  const [aiHint, setAiHint] = useState("");

  const handleSubmitSolution = async () => {
    if (!onSubmitCode) return;

    setIsSubmitting(true);
    setTab("output"); // Immediately switch to the output tab

    try {
      // Call the parent function and wait for the result
      const result = await onSubmitCode(code);

      // Directly update state with the validation result
      const validationResult = result.validation_result || {};
      setOutput(validationResult.output || "");
      setError(validationResult.error || "");
      setPassed(validationResult.passed);
    } catch (err) {
      // This will catch errors from the submission process itself
      setError(err.message || "Error al enviar la solución.");
      setPassed(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGetHint = async () => {
    setIsLoadingHint(true);
    setAiHint("");
    try {
      const res = await getCodeHint({
        code,
        error,
        instruction: "Ayúdame a entender y corregir este error.",
      });
      setAiHint(res.content || res.hint || "No se pudo obtener una pista.");
    } catch (err) {
      setAiHint("No se pudo obtener ayuda de la IA.");
    }
    setIsLoadingHint(false);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex items-center justify-between border-b border-primary/40 mb-4">
        <div className="flex">
          <button
            className={`px-4 py-2 ${tab === "editor" ? "text-secondary font-bold text-lg border-b-2 border-primary" : "text-gray-400"}`}
            onClick={() => setTab("editor")}
          >
            Editor de código
          </button>
          <button
            className={`px-4 py-2 ${tab === "output" ? "text-secondary font-bold border-b-2 border-primary" : "text-gray-400"}`}
            onClick={() => setTab("output")}
          >
            Salida
          </button>
        </div>
        <div className="flex gap-2">
          {/* MODIFIED: Conditional rendering for Submit Solution button */}
          {onSubmitCode && !isCorrect && (
            <Button
              onClick={handleSubmitSolution}
              disabled={isSubmitting} // Disable if already submitting
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {isSubmitting ? "Enviando..." : "Enviar Solución"}
            </Button>
          )}
        </div>
      </div>
      {/* Tab Content */}
      <div className="flex-1 min-h-0">
        {tab === "editor" && (
          <div>
            <CodeEditor
              initialCode={code}
              onChange={setCode}
              // The onExecute prop has been removed as there is no "Run Code" button.
            />
          </div>
        )}
        {tab === "output" && (
          <div className="mt-2">
            {/* Show pass/fail status */}
            {passed !== null && (
              <div className="mb-2">
                <span className={passed ? "text-green-500 font-bold" : "text-red-500 font-bold"}>
                  {passed ? "¡Correcto!" : "Incorrecto"}
                </span>
              </div>
            )}
            <OutputDisplay output={output} error={error} />
            {error && (
              <>
                <div className="flex gap-2 mt-2">
                  <Button onClick={handleGetHint} disabled={isLoadingHint} className="bg-primary/10 text-primary hover:bg-primary/20">
                    {isLoadingHint ? "Obteniendo pista..." : "Pedir pista IA"}
                  </Button>
                </div>
                {aiHint && (
                  <div className="mt-4 p-3  bg-primary/10 text-white rounded-xl">
                    <strong className="text-primary">Pista IA:</strong> {aiHint}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
