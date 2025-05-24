import React, { useEffect, useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Button } from '@nextui-org/react'; // Assuming NextUI is used
import { PlayCircleIcon } from '@heroicons/react/24/solid'; // Example Icon
import progressService from '../services/progressService';
import { useAuth } from '../hooks/useAuth'; // Assuming you have an auth hook

const ContinueLearningButton = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth(); // Or however you get user info
  const [lastAccessed, setLastAccessed] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated && user) {
      progressService.getLastAccessed()
        .then(data => {
          setLastAccessed(data);
          setIsLoading(false);
        })
        .catch(error => {
          console.error("Error fetching last accessed content:", error);
          setIsLoading(false);
          // Potentially handle error, e.g., if user has no progress yet
        });
    }
  }, [isAuthenticated, user]);

  const handleContinueLearning = () => {
    if (lastAccessed) {
      const { course_id, module_id, lesson_id, exercise_id } = lastAccessed;
      // Navigate to the most specific point of last access
      if (lesson_id) { // Includes exercise_id check implicitly if you structure URLs that way
        // If your lesson page can focus on an exercise, construct URL accordingly
        // For now, navigating to the lesson page.
        navigate({ to: `/courses/${course_id}/modules/${module_id}/lessons/${lesson_id}` });
      } else if (module_id) {
        navigate({ to: `/courses/${course_id}/modules/${module_id}` });
      } else if (course_id) {
        navigate({ to: `/courses/${course_id}` });
      }
    } else {
      // Maybe navigate to a general courses page or dashboard
      navigate({ to: '/dashboard/courses' });
    }
  };

  if (!isAuthenticated || isLoading || !lastAccessed) {
    // Don't show the button if not authenticated, loading, or no last accessed data
    // Or show a disabled state or a generic "Start Learning" button
    return null;
  }

  // Customize button text based on what was last accessed if desired
  let buttonText = "Continuar Aprendiendo";
  // Example: if (lastAccessed.lesson_id) buttonText = "Continuar Lección";

  return (
    <Button
      color="primary"
      auto
      ghost
      icon={<PlayCircleIcon className="h-5 w-5" />}
      onClick={handleContinueLearning}
      css={{ marginTop: '$4' }} // Example styling
    >
      {buttonText}
    </Button>
  );
};

export default ContinueLearningButton;
