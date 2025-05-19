import { Link } from '@tanstack/react-router';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@components/ui/card';
import { Badge } from '@components/ui/badge';
import { Progress } from '@components/ui/progress';
import { Button } from '@components/ui/button';
import FadeContent from '../ui/fade-content.jsx';


export function ModuleCard({ module, progress }) {
  const progressPercentage = progress?.percentage || 0;

  return (
    <FadeContent blur={true} duration={1000} easing="ease-out" initialOpacity={0} delay={700}>
    <Card className="overflow-hidden mt-6 cursor-default transition-transform duration-300 ease-out hover:scale-105 border-dark-light hover:border-primary h-full flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex justify-between">
            <Badge variant={
              module.level === 'beginner' ? 'default' :
              module.level === 'intermediate' ? 'secondary' :
              'destructive'
            }>
              {module.level}
            </Badge>
            <Badge className="bg-secondary hover:bg-secondary text-dark">{module.lessonCount} Lección</Badge>
          </div>
          <CardTitle className="text-2xl font-bold">{module.title}</CardTitle>
          <CardDescription>{module.description}</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col justify-end">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progreso</span>
              <span>{progressPercentage}%</span>
            </div>
            <Progress value={progressPercentage} className="h-2" />
          </div>
        </CardContent>
        <CardFooter>
          <Button asChild className="w-full hover:bg-primary-opaQUE">
            <Link to={`/module/${module.id}`}>
              {progressPercentage > 0 ? 'Continuar Aprendiendo' : 'Comenzar Lección'}
            </Link>
          </Button>
        </CardFooter>
      </Card>
    </FadeContent>
  );
}
