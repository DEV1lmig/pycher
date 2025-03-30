// filepath: /home/dev1mig/Documents/projects/pycher/frontend/src/components/modules/ModuleCard.jsx
import { Link } from '@tanstack/router';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';

export function ModuleCard({ module, progress }) {
  const progressPercentage = progress?.percentage || 0;

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex justify-between">
          <Badge variant={
             module.level === 'beginner' ? 'default' :
             module.level === 'intermediate' ? 'secondary' :
             'destructive'
          }>
            {module.level}
          </Badge>
          <Badge variant="outline">{module.lessonCount} lessons</Badge>
        </div>
        <CardTitle className="text-xl">{module.title}</CardTitle>
        <CardDescription>{module.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progress</span>
            <span>{progressPercentage}%</span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>
      </CardContent>
      <CardFooter>
        <Button asChild className="w-full">
          <Link to={`/module/${module.id}`}>
            {progressPercentage > 0 ? 'Continue Learning' : 'Start Learning'}
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
