import { useState } from "react";
import { CodeEditor } from "./CodeEditor";
import { Button } from "../ui/button";
import { OutputDisplay } from "@/components/editor/OutputDisplay";
import { executeCode } from "@/services/executionService"; // <-- import this

export default function LessonCodeExecutor({ initialCode = "" }) {
  const [code, setCode] = useState(initialCode);
  const [output, setOutput] = useState("");
  const [error, setError] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);

  const handleExecute = async () => {
    setIsExecuting(true);
    setOutput("");
    setError("");
    try {
      const result = await executeCode(code);
      setOutput(result.output || "");
      setError(result.error || "");
    } catch (err) {
      setError("Network error: " + err.message);
    }
    setIsExecuting(false);
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
      </div>
      <OutputDisplay output={output} error={error} />
    </div>
  );
}
