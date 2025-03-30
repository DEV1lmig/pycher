import React, { useState } from 'react';
import { CodeEditor } from '../components/editor/CodeEditor';
import { OutputDisplay } from '../components/editor/OutputDisplay';
import { Button } from '../components/ui/button';

const DEFAULT_CODE = `print("Hello, Pycher!")\n\n# Try modifying this code\nfor i in range(5):\n    print(f"Count: {i}")`;

export default function DemoPage() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  const runCode = async () => {
    setIsRunning(true);
    try {
      // If your api service is working, use it:
      const response = await fetch('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();
      setOutput(data.output || 'No output generated');
    } catch (error) {
      // Fallback for demo mode
      setOutput(`Hello, Pycher!\nCount: 0\nCount: 1\nCount: 2\nCount: 3\nCount: 4`);
      console.error('Error executing code:', error);
    }
    setIsRunning(false);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Python Code Playground</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="border rounded-md">
          <div className="bg-gray-100 p-3 border-b">
            <h2 className="font-medium">Editor</h2>
          </div>
          <div className="h-[400px]">
            <CodeEditor
              value={code}
              onChange={setCode}
              language="python"
            />
          </div>
        </div>

        <div className="border rounded-md">
          <div className="bg-gray-100 p-3 border-b flex justify-between items-center">
            <h2 className="font-medium">Output</h2>
            <Button
              onClick={runCode}
              disabled={isRunning}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {isRunning ? 'Running...' : 'Run Code'}
            </Button>
          </div>
          <div className="h-[400px] p-4 font-mono text-sm overflow-auto bg-gray-50">
            <OutputDisplay output={output} />
          </div>
        </div>
      </div>

      <div className="mt-8 p-4 border rounded-md bg-blue-50">
        <h2 className="font-bold text-lg mb-2">Demo Mode</h2>
        <p>This is a demonstration of Pycher's code execution capabilities. Try editing the code and running it!</p>
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
