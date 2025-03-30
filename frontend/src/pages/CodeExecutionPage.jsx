import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { MainLayout } from '../components/layout/MainLayout';
import { CodeEditor } from '../components/editor/CodeEditor';
import { OutputDisplay } from '../components/editor/OutputDisplay';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

// Example code for initial content
const initialCode = `# Welcome to the Python Learning Platform!
# Try running this simple example:

def greet(name):
    return f"Hello, {name}! Welcome to Python learning."

message = greet("Student")
print(message)

# Now try modifying this code and run it again
`;

export default function CodeExecutionPage() {
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');

  const executeMutation = useMutation({
    mutationFn: async (code) => {
      const { data } = await apiClient.post('/api/v1/execute', {
        code,
        timeout: 5 // 5-second timeout
      });
      return data;
    },
    onSuccess: (data) => {
      setOutput(data.output || '');
      setError(data.error || '');
    },
    onError: (error) => {
      setOutput('');
      setError('Failed to execute code: ' + error.message);
    },
  });

  const handleExecuteCode = async (code) => {
    return executeMutation.mutateAsync(code);
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Python Playground</h1>
          <p className="text-muted-foreground">
            Write and execute Python code in real-time
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Code Editor</CardTitle>
            </CardHeader>
            <CardContent>
              <CodeEditor
                initialCode={initialCode}
                onExecute={handleExecuteCode}
              />
              <OutputDisplay output={output} error={error} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Instructions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                This is your interactive Python playground where you can experiment with Python code.
              </p>
              <ol className="list-decimal list-inside space-y-2">
                <li>Write Python code in the editor</li>
                <li>Click the "Run Code" button to execute</li>
                <li>See the output below the editor</li>
                <li>Fix any errors that appear in the "Errors" tab</li>
              </ol>
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}
