import { useEffect, useState } from "react";
import { CourseCards } from "@/components/dashboard/CourseCards";
import { getAllCourses } from "@/services/contentService";
import { getCourseProgressSummary } from "@/services/progressService"; // Import this!
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen } from "lucide-react";

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);
  const [progressMap, setProgressMap] = useState({});

  useEffect(() => {
    getAllCourses().then(async (coursesData) => {
      setCourses(coursesData);
      // Fetch progress for each course in parallel
      const progressEntries = await Promise.all(
        coursesData.map(async (course) => {
          try {
            const progress = await getCourseProgressSummary(course.id);
            return [course.id, progress];
          } catch {
            return [course.id, null];
          }
        })
      );
      // Build a map: { [courseId]: progressObj }
      setProgressMap(Object.fromEntries(progressEntries));
    });
  }, []);

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
