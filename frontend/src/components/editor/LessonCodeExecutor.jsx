import { useState, useEffect } from "react"; // Import useEffect
import { CodeEditor } from "./CodeEditor";
import { Button } from "../ui/button";
import { OutputDisplay } from "@/components/editor/OutputDisplay";
import { executeCode } from "@/services/executionService";
import { getCodeHint } from "@/services/aiService";

export default function LessonCodeExecutor({
  initialCode = "",
  exerciseId,
  onSubmitCode,
  isSubmitting,
  isCorrect,
  onRunResult,
  currentUserStdin,
}) {
  const [tab, setTab] = useState("editor");
  const [code, setCode] = useState(initialCode);
  const [output, setOutput] = useState("");
  const [error, setError] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [aiHint, setAiHint] = useState("");
  const [isLoadingHint, setIsLoadingHint] = useState(false);
  const [passed, setPassed] = useState(null);
  // New state to control visibility of the submit button
  const [canSubmitSolution, setCanSubmitSolution] = useState(false);

  // Effect to hide submit button if code changes after a successful execution
  useEffect(() => {
    setCanSubmitSolution(false); // Reset when code changes
  }, [code]);

  const handleExecute = async () => {
    setIsExecuting(true);
    setOutput("");
    setError("");
    setAiHint("");
    setPassed(null);
    setCanSubmitSolution(false); // Hide submit button before execution
    try {
      const result = await executeCode({
        exerciseId,
        code,
        inputData: currentUserStdin,
      });
      setOutput(result.output || "");
      setError(result.error || "");
      setPassed(result.passed ?? null);
      setTab("output");
      if (onRunResult) onRunResult(result);

      // If execution had no errors, allow submission
      if (!result.error) {
        setCanSubmitSolution(true);
      }

    } catch (err) {
      setOutput("");
      setError("Network error: " + (err.detail || err.message));
      setPassed(false);
      setTab("output");
      setCanSubmitSolution(false); // Ensure it's false on network or other catchable errors
    }
    setIsExecuting(false);
  };

  const handleSubmitSolution = async () => {
    if (onSubmitCode) {
      await onSubmitCode(code);
      // After submission, the `isCorrect` prop will eventually update from the parent.
      // If the submission was successful and `isCorrect` becomes true,
      // the button will be hidden by the `!isCorrect` condition.
      // If submission failed, `canSubmitSolution` remains true, allowing another attempt
      // unless `isCorrect` changed or code was modified.
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
          <Button
            onClick={handleExecute}
            disabled={isExecuting || isSubmitting}
            className="bg-primary hover:bg-primary/80 text-white"
          >
            {isExecuting ? "Ejecutando..." : "Ejecutar Código"}
          </Button>
          {/* MODIFIED: Conditional rendering for Submit Solution button */}
          {onSubmitCode && !isCorrect && canSubmitSolution && (
            <Button
              onClick={handleSubmitSolution}
              disabled={isSubmitting || isExecuting} // Disable if already submitting or executing
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
              onExecute={handleExecute}
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
