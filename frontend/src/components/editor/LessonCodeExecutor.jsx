import { useState } from "react";
import { CodeEditor } from "./CodeEditor";
import { Button } from "../ui/button";
import { OutputDisplay } from "@/components/editor/OutputDisplay";
import { executeCode } from "@/services/executionService";
import { getCodeHint } from "@/services/aiService";

export default function LessonCodeExecutor({ initialCode = "" }) {
  const [tab, setTab] = useState("editor");
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
      setTab("output");
    } catch (err) {
      setOutput("");
      setError("Network error: " + err.message);
      setTab("output");
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
      <Button
        onClick={handleExecute}
        disabled={isExecuting}
        className="bg-primary hover:bg-primary/80 text-white"
      >
        {isExecuting ? "Ejecutando..." : "Ejecutar Código"}
      </Button>
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
            <OutputDisplay output={output} error={error} />
            {error && (
              <>
                <div className="flex gap-2 mt-2">
                  <Button onClick={handleGetHint} disabled={isLoadingHint}  className="bg-primary/10 text-primary hover:bg-primary/20">
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