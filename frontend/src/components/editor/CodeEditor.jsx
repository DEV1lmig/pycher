import Editor from '@monaco-editor/react';
import { Button } from '../ui/button';
import { PlayIcon, RotateCwIcon } from 'lucide-react';

export function CodeEditor({ initialCode = '', onChange }) {

  const handleEditorChange = (value) => {
    onChange(value);
  };

  return (
    <div className="border border-primary-opaque/50 rounded-md overflow-hidden">
      <div className="bg-muted p-2 flex justify-between items-center">
        <div className="font-medium">Python Editor</div>
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
