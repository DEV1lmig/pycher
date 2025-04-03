import { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Button } from '../ui/button';
import { PlayIcon, RotateCwIcon } from 'lucide-react';

export function CodeEditor({ initialCode = '', onExecute, onChange }) {
  const [code, setCode] = useState(initialCode);
  const [isExecuting, setIsExecuting] = useState(false);

  const handleEditorChange = (value) => {
    // Make sure this is calling the onChange prop with the new value
    onChange(value);
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      await onExecute(code);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="border rounded-md overflow-hidden">
      <div className="bg-muted p-2 flex justify-between items-center">
        <div className="font-medium">Python Editor</div>
        <div className="flex gap-2">
          <Button
            onClick={handleExecute}
            disabled={isExecuting}
            size="sm"
          >
            {isExecuting ? (
              <>
                <RotateCwIcon className="mr-2 h-4 w-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <PlayIcon className="mr-2 h-4 w-4" />
                Run Code
              </>
            )}
          </Button>
        </div>
      </div>
      <Editor
        height="400px"
        defaultLanguage="python"
        defaultValue={initialCode}
        onChange={handleEditorChange}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 14,
          tabSize: 4,
          automaticLayout: true,
        }}
      />
    </div>
  );
}
