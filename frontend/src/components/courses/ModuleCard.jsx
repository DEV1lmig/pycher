import { Link } from '@tanstack/react-router';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Lock } from 'lucide-react';
import FadeContent from '@/components/ui/fade-content.jsx';

export function ModuleCard({ module, progress, isLocked = false }) {
  const progressPercentage = progress?.percentage || 0;

  return (
    <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100}>
      <Card className={`overflow-hidden mt-6 cursor-default transition-transform duration-300 ease-out h-full flex flex-col ${
        isLocked
          ? "bg-gray-800/10 border-gray-600 opacity-60"
          : "hover:bg-dark hover:border-primary hover:scale-105 bg-primary-opaque/10 border-dark-light border-primary-opaque/0"
      }`}>
        <CardHeader className="pb-3">
          <div className="flex justify-between items-start">
            <div className="flex gap-2">
              <Badge variant={
                module.level === 'beginner' ? 'default' :
                module.level === 'intermediate' ? 'secondary' :
                'destructive'
              }>
                {module.level}
              </Badge>
              <Badge className="bg-secondary hover:bg-secondary text-dark">
                {module.lessonCount || 0} Lecciones
              </Badge>
            </div>
            {isLocked && <Lock className="h-5 w-5 text-gray-400" />}
          </div>
          <CardTitle className={`text-2xl font-bold ${isLocked ? 'text-gray-400' : 'text-white'}`}>
            {module.title}
          </CardTitle>
          <CardDescription className={isLocked ? 'text-gray-500' : ''}>
            {module.description}
          </CardDescription>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col justify-end">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className={isLocked ? 'text-gray-500' : 'text-gray-300'}>Progreso</span>
              <span className={isLocked ? 'text-gray-500' : 'text-white'}>{progressPercentage}%</span>
            </div>
            <Progress
              value={progressPercentage}
              className={`h-2 ${isLocked ? 'opacity-50' : ''}`}
            />
          </div>
        </CardContent>

        <CardFooter>
          {isLocked ? (
            <div className="w-full text-center py-2 text-gray-500 text-sm">
              <Lock className="h-4 w-4 inline mr-2" />
              Módulo bloqueado
            </div>
          ) : (
            <Button asChild className="w-full hover:bg-primary-opaque">
              <Link to={`/module/${module.id}`}>
                {progressPercentage > 0 ? 'Continuar Aprendiendo' : 'Comenzar Lección'}
              </Link>
            </Button>
          )}
        </CardFooter>
      </Card>
    </FadeContent>
  );
}
