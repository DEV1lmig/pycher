import { CourseCards } from "@/components/dashboard/CourseCards";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen } from "lucide-react";
import { useCourses } from "@/hooks/useContentQueries"; // 1. Import the new hook
import { Skeleton } from "@/components/ui/skeleton"; // 2. Import Skeleton for loading state

export default function CoursesPage() {
  // 3. Use the custom hook to get data, loading, and error states
  const { courses, progressMap, isLoading, error } = useCourses();

  // 4. Handle the loading state
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="m-6">
          <FadeContent blur={true} duration={500} easing="ease-out" initialOpacity={0} delay={100}>
            <Breadcrumbs
              items={[
                { label: "Inicio", href: "/home", icon: <Home size={16} /> },
                { label: "Cursos", icon: <BookOpen size={16} /> },
              ]}
            />
            <h3 className="text-2xl font-bold text-white">Cursos disponibles para ti</h3>
          </FadeContent>
          <div className="my-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 cursor-default gap-6">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-64 w-full bg-primary-opaque/20" />)}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // 5. Handle any errors during fetching
  if (error) {
    return (
      <DashboardLayout>
        <div className="m-6 text-center text-red-400">
          <p>Error al cargar los cursos: {error.message}</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="m-6">
        <FadeContent blur={true} duration={500} easing="ease-out" initialOpacity={0} delay={100}>
          <Breadcrumbs
            items={[
              { label: "Inicio", href: "/home", icon: <Home size={16} /> },
              { label: "Cursos", icon: <BookOpen size={16} /> },
            ]}
          />
          <h3 className="text-2xl font-bold text-white">Cursos disponibles para ti</h3>
        </FadeContent>
        <div className="my-6">
          <CourseCards courses={courses} progressMap={progressMap} />
        </div>
      </div>
    </DashboardLayout>
  );
}
