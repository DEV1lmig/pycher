import React, { useState } from 'react';
import { CodeEditor } from '../components/editor/CodeEditor';
import { OutputDisplay } from '../components/editor/OutputDisplay';
import { executeCode } from '../services/executionService';
import { getCodeHint } from '../services/aiService';
import { Button } from '../components/ui/button';

const DEFAULT_CODE = `print("Hello, Pycher!")\n\n# Try modifying this code\nfor i in range(5):\n    print(f"Count: {i}")`;

export default function DemoPage() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [aiHelp, setAiHelp] = useState('');
  const [isLoadingAiHelp, setIsLoadingAiHelp] = useState(false);

  // Handler for code execution
  const handleExecuteCode = async (codeToExecute) => {
    setIsExecuting(true);
    setAiHelp('');

    try {
      const result = await executeCode(codeToExecute || code);

      // Always set the output
      setOutput(result.output || '');

      // Set error if present
      setError(result.error || '');

      // If there's an error and it's not trivial, offer AI help
      if (result.error && result.error.length > 10) {
        // Show button to get AI help
      }
    } catch (err) {
      console.error('Error executing code:', err);
      setError('Network error: Failed to execute code. Please try again.');
      setOutput('');
    } finally {
      setIsExecuting(false);
    }
  };

  // Function to request AI help with the error
  const requestAiHelp = async () => {
    if (!error) return;

    setIsLoadingAiHelp(true);
    try {
      const help = await getCodeHint({
        code: code,
        error: error,
        instruction: "Fix the error in this code",
        difficulty: 'beginner'
      });

      setAiHelp(help.hint || "Sorry, I couldn't generate a helpful hint at this time.");
    } catch (err) {
      console.error("Error getting AI help:", err);
      setAiHelp("Unable to get AI assistance at this time.");
    } finally {
      setIsLoadingAiHelp(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Python Code Playground</h1>

      <div className="mb-6">
        <CodeEditor
          initialCode={DEFAULT_CODE}
          onExecute={handleExecuteCode}
        />

        <div className="mt-4 flex justify-end">
          <Button
            onClick={() => handleExecuteCode(code)}
            disabled={isExecuting}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            {isExecuting ? 'Running...' : 'Run Code'}
          </Button>
        </div>
      </div>

      <OutputDisplay
        output={output}
        error={error}
      />

      {/* Show AI Help Button when there's an error */}
      {error && !aiHelp && (
        <div className="mt-4">
          <Button
            onClick={requestAiHelp}
            disabled={isLoadingAiHelp}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {isLoadingAiHelp ? 'Getting Help...' : 'Get AI Help with Error'}
          </Button>
        </div>
      )}

      {/* Display AI Help when available */}
      {aiHelp && (
        <div className="mt-4 p-4 bg-blue-50 rounded-md border border-blue-200">
          <h3 className="font-bold mb-2">AI Suggestion:</h3>
          <div className="whitespace-pre-wrap">{aiHelp}</div>
        </div>
      )}

      <div className="mt-8 p-4 border rounded-md bg-blue-50">
        <h2 className="font-bold text-lg mb-2">Demo Mode</h2>
        <p>This is a demonstration of Pycher's code execution capabilities. Try editing the code and running it!</p>
        <p className="mt-2">If your code has errors, you can request AI assistance to help fix them.</p>
        <p className="mt-2">In the full version, you'll have access to:</p>
        <ul className="list-disc ml-5 mt-2">
          <li>Interactive Python lessons</li>
          <li>Exercises with automated feedback</li>
          <li>AI-powered code explanations</li>
          <li>Learning progress tracking</li>
        </ul>
      </div>
    </div>
  );
}
