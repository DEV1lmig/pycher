import { Link } from '@tanstack/react-router';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Lock, CheckCircle, FileText } from 'lucide-react'; // Added FileText for exam icon
import FadeContent from '@/components/ui/fade-content.jsx';

export function ModuleCard({ module, progress, isLocked = false }) {
  const progressPercentage = progress?.progress_percentage || 0;
  const isCompleted = progress?.is_completed;
  const isExamModule = module.is_exam === true; // Explicitly check for true

  const cardClasses = `overflow-hidden mt-6 cursor-default transition-transform duration-300 ease-out h-full flex flex-col ${
    isLocked
      ? "bg-gray-800/10 border-gray-600 opacity-60"
      : "hover:bg-dark hover:border-primary hover:scale-105 bg-primary-opaque/10 border-dark-light border-primary-opaque/0"
  }`;

  const titleClasses = `text-2xl font-bold ${isLocked ? 'text-gray-400' : 'text-white'}`;
  const descriptionClasses = isLocked ? 'text-gray-500' : '';
  const progressTextClasses = isLocked ? 'text-gray-500' : 'text-gray-300';
  const progressValueTextClasses = isLocked ? 'text-gray-500' : 'text-white';
  const progressClasses = `h-2 ${isLocked ? 'opacity-50' : ''}`;

  const linkDestination = isExamModule
    ? `/courses/${module.course_id}/exam-interface` // Placeholder for actual exam page route
    : `/module/${module.id}`;

  const buttonText = isExamModule
    ? (isCompleted ? 'Examen Completado' : 'Ir al Examen')
    : (progressPercentage > 0 && !isCompleted ? 'Continuar Aprendiendo' : (isCompleted ? 'Módulo Completado' : 'Comenzar Módulo'));


  return (
    <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100}>
      <Card className={cardClasses}>
        <CardHeader className="pb-3">
          <div className="flex justify-between items-start">
            <div className="flex gap-2">
              {/* Level Badge (optional for exams or can be kept) */}
              {module.level && !isExamModule && (
                <Badge variant={
                  module.level === 'beginner' ? 'default' :
                  module.level === 'intermediate' ? 'secondary' :
                  'destructive'
                }>
                  {module.level}
                </Badge>
              )}
              {isExamModule ? (
                <Badge className="bg-red-500 hover:bg-red-600 text-white">
                  <FileText size={14} className="mr-1" /> Examen Final
                </Badge>
              ) : (
                <Badge className="bg-secondary hover:bg-secondary text-dark">
                  {module.lessonCount || 0} Lecciones
                </Badge>
              )}
            </div>
            {isLocked && <Lock className="h-5 w-5 text-gray-400" />}
            {!isLocked && isCompleted && (
              <CheckCircle className="h-5 w-5 text-green-400" />
            )}
          </div>
          <CardTitle className={titleClasses}>
            {module.title}
          </CardTitle>
          <CardDescription className={descriptionClasses}>
            {module.description}
          </CardDescription>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col justify-end">
          {/* Progress bar can be shown for exams too if progress indicates completion */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className={progressTextClasses}>Progreso</span>
              <span className={progressValueTextClasses}>{Math.round(progressPercentage)}%</span>
            </div>
            <Progress
              value={progressPercentage}
              className={progressClasses}
              indicatorClassName={isExamModule && isCompleted ? "bg-green-500" : (isExamModule ? "bg-red-500" : "bg-secondary")}
            />
          </div>
        </CardContent>

        <CardFooter>
          {isLocked ? (
            <div className="w-full text-center py-2 text-gray-500 text-sm">
              <Lock className="h-4 w-4 inline mr-2" />
              {isExamModule ? "Examen Bloqueado" : "Módulo bloqueado"}
            </div>
          ) : (
            <Button asChild className={`w-full ${isExamModule && isCompleted ? "bg-green-600 hover:bg-green-700" : (isExamModule ? "bg-red-500 hover:bg-red-600" : "hover:bg-primary-opaque")}`} disabled={isExamModule && isCompleted && isLocked}>
              <Link to={linkDestination} disabled={isExamModule && isCompleted}>
                {buttonText}
              </Link>
            </Button>
          )}
        </CardFooter>
      </Card>
    </FadeContent>
  );
}
