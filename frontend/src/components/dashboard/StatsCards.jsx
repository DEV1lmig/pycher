import { BookOpen, Code } from "lucide-react" // Removed Clock
import AnimatedContent from '../ui/animated-content'
import { useEffect, useState } from "react";
import { getUserEnrollments } from "@/services/userService"; // Import service to get enrollments

export function StatsCards() {
  const [enrolledCoursesCount, setEnrolledCoursesCount] = useState(0);
  // Placeholder for completed exercises - ideally, this would come from a dedicated backend endpoint
  const [completedExercisesCount, setCompletedExercisesCount] = useState("N/A");

  useEffect(() => {
    getUserEnrollments()
      .then(enrollments => {
        setEnrolledCoursesCount(enrollments.length);
        // TODO: Fetch actual completed exercises count.
        // This currently requires iterating through all lessons and their exercises,
        // which is inefficient from the frontend.
        // A backend endpoint like /api/v1/users/me/completed-exercises-count would be better.
        // For now, we can set a placeholder or a mock value if needed.
        // Example: setCompletedExercisesCount(calculateCompletedExercises(enrollments));
      })
      .catch(error => {
        console.error("Error fetching user enrollments for stats:", error);
        setEnrolledCoursesCount(0); // Default to 0 on error
      });
  }, []);

  const stats = [
    {
      title: "Cursos Activos",
      value: enrolledCoursesCount.toString(),
      icon: BookOpen,
      color: "bg-[#5f2dee]/10 text-primary",
    },
    {
      title: "Ejercicios Completados",
      value: completedExercisesCount.toString(), // Display the fetched or placeholder value
      icon: Code,
      color: "bg-[#f2d231]/10 text-[#f2d231]",
    },
    // "Horas de Estudio" card removed
  ];

  const bgColors = [
    "bg-[#5f2dee]/10",
    "bg-[#f2d231]/10",
    // Removed third color as there are only two cards now
  ];

  return (
    <AnimatedContent
      distance={40}
      direction="vertical"
      reverse={true}
      config={{ tension: 100, friction: 10 }}
      initialOpacity={0}
      animateOpacity
      scale={1}
      threshold={0.2}
      delay={100}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4"> {/* Changed md:grid-cols-3 to md:grid-cols-2 */}
        {stats.map((stat, index) => (
          <div
            key={index}
            className={`rounded-lg p-4 hover:scale-105 transition-transform duration-300 ${bgColors[index % bgColors.length]}`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-gray-400 text-sm">{stat.title}</p>
                <p className="text-2xl font-bold mt-1">{stat.value}</p>
              </div>
              <div className={`p-2 rounded-md ${stat.color}`}>
                <stat.icon className="h-5 w-5" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </AnimatedContent>
  );
}
