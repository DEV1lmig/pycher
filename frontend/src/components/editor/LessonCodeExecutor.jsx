import { useState } from "react";
import { CodeEditor } from "./CodeEditor";
import { Button } from "../ui/button";
import { OutputDisplay } from "@/components/editor/OutputDisplay";
import { executeCode } from "@/services/executionService";
import { getCodeHint } from "@/services/aiService";

export default function LessonCodeExecutor({ initialCode = "" }) {
  const [code, setCode] = useState(initialCode);
  const [output, setOutput] = useState("");
  const [error, setError] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [aiHint, setAiHint] = useState("");
  const [isLoadingHint, setIsLoadingHint] = useState(false);

  const handleExecute = async () => {
    setIsExecuting(true);
    setOutput("");
    setError("");
    setAiHint("");
    try {
      const result = await executeCode(code);
      setOutput(result.output || "");
      setError(result.error || "");
    } catch (err) {
      setError("Network error: " + err.message);
    }
    setIsExecuting(false);
  };

  const handleGetHint = async () => {
    setIsLoadingHint(true);
    setAiHint("");
    try {
      const res = await getCodeHint({
        code,
        error,
        instruction: "Ayúdame a entender y corregir este error."
      });
      setAiHint(res.content || res.hint || "No se pudo obtener una pista.");
    } catch (err) {
      setAiHint("No se pudo obtener ayuda de la IA.");
    }
    setIsLoadingHint(false);
  };

  return (
    <div>
      <CodeEditor
        initialCode={code}
        onChange={setCode}
        onExecute={handleExecute}
      />
      <div className="flex gap-2 mt-2">
        <Button onClick={handleExecute} disabled={isExecuting} className="bg-[#5f2dee] hover:bg-[#4f25c5] text-white">
          {isExecuting ? "Ejecutando..." : "Ejecutar Código"}
        </Button>
        <Button onClick={handleGetHint} disabled={isLoadingHint || !error} variant="outline">
          {isLoadingHint ? "Obteniendo pista..." : "Pedir pista IA"}
        </Button>
      </div>
      <OutputDisplay output={output} error={error} />
      {aiHint && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-blue-900">
          <strong>Pista IA:</strong> {aiHint}
        </div>
      )}
    </div>
  );
}
