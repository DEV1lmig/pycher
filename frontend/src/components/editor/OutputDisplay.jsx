import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

export function OutputDisplay({ output = '', error = '' }) {
  const hasError = Boolean(error);

  // Automatically switch to error tab when there's an error
  return (
    <div className="border rounded-md overflow-hidden mt-4">
      <Tabs defaultValue={hasError ? 'error' : 'output'} className="w-full">
        <div className="bg-muted p-2">
          <TabsList>
            <TabsTrigger value="output">Output</TabsTrigger>
            <TabsTrigger value="error" disabled={!hasError} className="data-[state=active]:text-red-500 data-[state=active]:font-medium">
              {hasError && <span className="w-2 h-2 rounded-full bg-red-500 mr-2 animate-pulse"></span>}
              Errors
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="output" className="m-0">
          <pre className="bg-black text-white p-4 overflow-auto h-32 whitespace-pre-wrap">
            {output || 'No output yet. Run your code to see the results.'}
          </pre>
        </TabsContent>

        <TabsContent value="error" className="m-0">
          <pre className="bg-black text-red-400 p-4 overflow-auto h-32 whitespace-pre-wrap">
            {error || 'No errors.'}
          </pre>
        </TabsContent>
      </Tabs>
    </div>
  );
}
