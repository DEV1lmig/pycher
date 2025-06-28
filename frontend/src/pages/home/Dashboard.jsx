import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { CourseCards } from "@/components/dashboard/CourseCards";
import { WelcomeHeader } from "@/components/dashboard/WelcomeHeader";
import { StatsCards } from "@/components/dashboard/StatsCards";
import FadeContent from "../../components/ui/fade-content.jsx";
import { useCourses, useDashboardStats } from "@/hooks/useContentQueries.js";
import { Skeleton } from "@/components/ui/skeleton.jsx";

export default function DashboardPage() {
  // Fetch courses and their progress using our custom hook
  const { courses, progressMap, isLoading: coursesLoading, error: coursesError } = useCourses();

  // Fetch dashboard stats using our new custom hook
  const { data: completedExercisesCount, isLoading: statsLoading, error: statsError } = useDashboardStats();

  const isLoading = coursesLoading || statsLoading;
  const error = coursesError || statsError;

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex flex-col gap-6 p-6">
          <WelcomeHeader />
          {/* Skeleton for StatsCards */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Skeleton className="h-28 w-full bg-primary-opaque/20" />
            <Skeleton className="h-28 w-full bg-primary-opaque/20" />
            <Skeleton className="h-28 w-full bg-primary-opaque/20" />
            <Skeleton className="h-28 w-full bg-primary-opaque/20" />
          </div>
          <section>
            <FadeContent blur={true} duration={500} easing="ease-out" initialOpacity={0} delay={250}>
              <h2 className="text-2xl font-bold text-white mb-4">Nuestros Cursos</h2>
              <p className="text-gray-300 mb-6">
                Selecciona el curso que deseas estudiar y comienza tu viaje en el mundo de Python
              </p>
            </FadeContent>
            {/* Skeleton for CourseCards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 cursor-default gap-6">
              {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-64 w-full bg-primary-opaque/20" />)}
            </div>
          </section>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="p-6 text-center text-red-400">
          <p>Error al cargar el dashboard: {error.message}</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6 p-6">
        <WelcomeHeader />
        <StatsCards completedExercisesCount={completedExercisesCount}/>
        <section>
          <FadeContent blur={true} duration={500} easing="ease-out" initialOpacity={0} delay={250}>
          <h2 className="text-2xl font-bold text-white mb-4">Nuestros Cursos</h2>
          <p className="text-gray-300 mb-6">
            Selecciona el curso que deseas estudiar y comienza tu viaje en el mundo de Python
          </p>
          </FadeContent>
          <CourseCards courses={courses} progressMap={progressMap} />
        </section>
      </div>
    </DashboardLayout>
  )
}
