import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ClipboardList } from 'lucide-react';
import { Link } from "@tanstack/react-router";

export function ExamCard({ exam, isLocked, onStart }) {
  return (
    <Card className={`overflow-hidden mt-6 cursor-default transition-transform duration-300 ease-out h-full flex flex-col ${isLocked ? 'opacity-60 pointer-events-none' : ''}`}>
      <CardHeader className="pb-3 flex flex-row items-center gap-3">
        <ClipboardList className="w-8 h-8 text-primary" />
        <div>
          <CardTitle className={`text-2xl font-bold ${isLocked ? 'text-gray-400' : 'text-white'}`}>
            {exam.title || "Examen Final"}
          </CardTitle>
          <CardDescription className={isLocked ? 'text-gray-500' : ''}>
            {exam.description || "Demuestra tus conocimientos en este examen final."}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-end">
        <div className="text-gray-300 text-sm mb-2">
          {exam.instructions}
        </div>
      </CardContent>
      <CardFooter>
        <Button
          asChild
          variant="secondary"
          disabled={isLocked}
        >
          <Link to={`/courses/${exam.course_id}/exam`}>
            Comenzar Examen
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
