import { Link } from "@tanstack/react-router";
import { Lock, CheckCircle, Star, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function ExamStatusCard({ examExercise, isUnlocked, isCompleted, courseId }) {
  // UPDATE: The link now correctly points to the static exam interface route.
  // The backend will determine the specific exercise when this page loads.
  const linkTarget = `/courses/${courseId}/exam-interface`;

  const getCardState = () => {
    if (isCompleted) {
      return {
        cardClass: "bg-gradient-to-br from-green-500/20 to-green-400/20 border-green-500/30 hover:scale-[1.02] transition-transform duration-300",
        title: examExercise.title,
        icon: <CheckCircle className="h-4 w-4 text-green-400" />,
        // UPDATE: Button text changed for review mode.
        buttonText: "Revisar Examen",
        buttonVariant: "secondary",
        isDisabled: false,
        description: "¡Felicidades! Has completado y aprobado el examen final de este curso.",
        topRightIcon: <CheckCircle className="h-5 w-5 text-green-400" />
      };
    }
    if (isUnlocked) {
      return {
        cardClass: "bg-gradient-to-br from-primary/20 to-blue/20 border-primary/30 hover:scale-[1.02] transition-transform duration-300",
        title: examExercise.title,
        icon: null,
        buttonText: "Comenzar Examen",
        buttonVariant: "default",
        isDisabled: false,
        description: examExercise.description,
        topRightIcon: <Star className="h-5 w-5 text-secondary" />
      };
    }
    return {
      cardClass: "bg-gradient-to-br from-gray-500/10 to-gray-400/10 border-gray-500/20 opacity-60",
      title: examExercise.title,
      icon: null,
      buttonText: "Bloqueado",
      buttonVariant: "outline",
      isDisabled: true,
      description: "Completa todos los módulos del curso para desbloquear el examen final.",
      topRightIcon: <Lock className="h-5 w-5 text-gray-400" />
    };
  };

  const state = getCardState();

  const cardContent = (
    <CardContent className="p-4 flex flex-col h-full">
      <div className="flex items-start justify-between mb-3 flex-grow">
        <div className="flex-1">
          <h3 className="font-semibold text-white mb-1 text-sm flex items-center gap-2">
            {state.title}
            {state.icon}
          </h3>
          <p className="text-gray-300 text-xs line-clamp-2">{state.description}</p>
        </div>
        <div className="ml-2 flex-shrink-0">
          {state.topRightIcon}
        </div>
      </div>

      <Button
        size="sm"
        variant={state.buttonVariant}
        className="w-full text-xs"
        disabled={state.isDisabled}
      >
        {state.buttonText}
      </Button>
    </CardContent>
  );

  return (
    <Card className={state.cardClass}>
      {/* UPDATE: The link is now enabled for both unlocked and completed (review) states */}
      {isUnlocked || isCompleted ? (
        <Link to={linkTarget} className="block h-full">
          {cardContent}
        </Link>
      ) : (
        cardContent
      )}
    </Card>
  );
}
