import { Link } from '@tanstack/react-router';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@components/ui/card';
import { Badge } from '@components/ui/badge';
import { Progress } from '@components/ui/progress';
import { Button } from '@components/ui/button';

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
