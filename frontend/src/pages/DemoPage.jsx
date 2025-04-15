import React, { useState, useEffect } from 'react';
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
  const [executionTime, setExecutionTime] = useState(null);
  const [errorSeverity, setErrorSeverity] = useState('none'); // 'none', 'syntax', 'runtime', 'logic'

  // Reset AI help when code changes
  useEffect(() => {
    setAiHelp('');
  }, [code]);

  // Handler for code execution
  const handleExecuteCode = async (codeToExecute) => {
    setIsExecuting(true);
    setAiHelp('');
    setErrorSeverity('none');

    // Log what's being executed for debugging
    console.log("Executing code:", codeToExecute || code);

    const startTime = performance.now();

    try {
      // Make sure we're passing the correct code to execute
      const result = await executeCode(codeToExecute || code);
      const endTime = performance.now();

      // Set execution time
      setExecutionTime((endTime - startTime).toFixed(0));

      // Set output regardless of error
      setOutput(result.output || '');

      // Process error if present
      if (result.error) {
        setError(result.error);

        // Determine error severity for better AI assistance
        if (result.error.includes('SyntaxError')) {
          setErrorSeverity('syntax');
        } else if (result.error.includes('TypeError') ||
                  result.error.includes('ValueError') ||
                  result.error.includes('NameError')) {
          setErrorSeverity('runtime');
        } else {
          setErrorSeverity('logic');
        }
      } else {
        setError('');
      }
    } catch (err) {
      console.error('Error executing code:', err);
      setError(`Network error: ${err.message}`);
      setErrorSeverity('network');
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
        instruction: `Analyze the error below and provide a detailed explanation of its potential causes and suggestions for fixing it.`
      });

      // Handle the new nested response structure
      if (help.error_analysis && typeof help.error_analysis === 'object') {
        // Extract the detailed error information
        const { explanation, cause, hint } = help.error_analysis;

        // Build a formatted response with all the useful information
        let formattedHelp = '';
        if (explanation) formattedHelp += `${explanation}\n\n`;
        if (cause) formattedHelp += `Cause: ${cause}\n\n`;
        if (hint) formattedHelp += `Hint: ${hint}`;

        setAiHelp(formattedHelp || "AI was unable to analyze this error in detail.");
      } else if (help.error_analysis || help.hint) {
        // Fallback for the previous format (direct strings)
        const analysis = help.error_analysis ? `${help.error_analysis}\n\n` : '';
        const hint = help.hint || '';
        setAiHelp(`${analysis}${hint}`);
      } else {
        setAiHelp("AI was unable to provide a detailed analysis of the error.");
      }
    } catch (err) {
      console.error("Error getting AI help:", err);
      setAiHelp("Unable to get AI assistance right now. Please try again later.");
    } finally {
      setIsLoadingAiHelp(false);
    }
  };

  // Function to apply AI suggestion directly to code editor
  const applyAiSuggestion = async () => {
    if (!error || !code) return;

    setIsLoadingAiHelp(true);
    try {
      const suggestion = await getCodeHint({
        code: code,
        error: error,
        instruction: "Fix this code by providing a corrected version. Only return the fixed code without explanations."
      });

      // Look for suggestions in the new nested structure
      if (suggestion.error_analysis?.corrected_code) {
        setCode(suggestion.error_analysis.corrected_code);
        setAiHelp('');
      } else if (suggestion.error_analysis?.hint) {
        // The hint might contain code suggestions
        setAiHelp(suggestion.error_analysis.hint);
      } else if (suggestion.hint || suggestion.error_analysis) {
        // Fallback to previous format
        setCode(suggestion.hint || suggestion.error_analysis);
        setAiHelp('');
      } else {
        setAiHelp("Couldn't generate a code fix automatically. Please review the error message and try to fix it manually.");
      }
    } catch (err) {
      console.error("Error getting AI suggestion:", err);
    } finally {
      setIsLoadingAiHelp(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Python Code Playground</h1>

      <div className="mb-6">
        <div className="bg-gray-100 p-3 border-b flex justify-between items-center rounded-t-md">
          <h2 className="font-medium">Editor</h2>
          <div>
            <Button
              onClick={() => setCode(DEFAULT_CODE)}
              variant="outline"
              size="sm"
              className="mr-2"
            >
              Reset Code
            </Button>
            <Button
              onClick={() => handleExecuteCode(code)}
              disabled={isExecuting}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {isExecuting ? 'Running...' : 'Run Code'}
            </Button>
          </div>
        </div>

        <div className="border rounded-b-md p-0">
          <CodeEditor
            initialCode={code} // Change from value to initialCode based on your component's API
            onChange={setCode}  // Make sure this properly calls the state setter
            language="python"
            height="350px"
            onExecute={() => handleExecuteCode(code)} // Add this to handle Ctrl+Enter execution
          />
        </div>
      </div>

      <div className="mb-4">
        <div className="bg-gray-100 p-3 border-b flex justify-between items-center rounded-t-md">
          <h2 className="font-medium">Output</h2>
          {executionTime && !isExecuting && (
            <span className="text-sm text-gray-500">
              Execution time: {executionTime}ms
            </span>
          )}
        </div>
        <OutputDisplay
          output={output}
          error={error}
        />
      </div>

      {/* AI Help Section */}
      <div className="mt-6">
        {error && !aiHelp && (
          <div className="flex justify-end">
            <Button
              onClick={requestAiHelp}
              disabled={isLoadingAiHelp}
              className="bg-blue-600 hover:bg-blue-700 text-white mr-2"
            >
              {isLoadingAiHelp ? 'Getting Help...' : 'Get AI Help'}
            </Button>

            <Button
              onClick={applyAiSuggestion}
              disabled={isLoadingAiHelp}
              variant="outline"
              className="border-blue-600 text-blue-600 hover:bg-blue-50"
            >
              Fix Code Automatically
            </Button>
          </div>
        )}

        {/* Display AI Help when available */}
        {aiHelp && (
          <div className="mt-4 p-4 bg-blue-50 rounded-md border border-blue-200">
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-bold text-blue-800">AI Suggestion:</h3>
              <Button
                onClick={() => setAiHelp('')}
                variant="ghost"
                size="sm"
                className="h-6 text-gray-500"
              >
                Dismiss
              </Button>
            </div>
            <div className="whitespace-pre-wrap prose max-w-none">
              {aiHelp}
            </div>
          </div>
        )}
      </div>

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

      {/* Sample Error Buttons for Testing */}
      <div className="mt-4 p-4 border border-dashed border-gray-300 rounded-md">
        <h3 className="font-medium mb-2">Test Error Handling</h3>
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={() => setCode('print("Hello World"\nprint(10/0)')}
            variant="outline"
            size="sm"
          >
            Test Runtime Error
          </Button>
          <Button
            onClick={() => setCode('print("Syntax Error Example"\nif True\n    print("Missing colon")')}
            variant="outline"
            size="sm"
          >
            Test Syntax Error
          </Button>
          <Button
            onClick={() => setCode('print("Name Error Example")\nprint(undefined_variable)')}
            variant="outline"
            size="sm"
          >
            Test Name Error
          </Button>
        </div>
      </div>
    </div>
  );
}
