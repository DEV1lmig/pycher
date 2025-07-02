import { useEffect, useState, useMemo } from "react";
import { CourseCards } from "@/components/dashboard/CourseCards";
import { getAllCourses } from "@/services/contentService";
import { useCourseAccess } from "@/hooks/useCourseAccess";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen } from "lucide-react";

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);
  const { userEnrollments } = useCourseAccess(); // Use the hook as the live source of truth

  // This effect now only fetches the static list of all available courses
  useEffect(() => {
    getAllCourses().then((coursesData) => {
      coursesData.sort((a, b) => a.id - b.id);
      setCourses(coursesData);
    });
  }, []);

  // This derived state creates the progress map. It will automatically
  // re-compute whenever the user's enrollments change.
  const progressMap = useMemo(() => {
    if (!userEnrollments) return {};
    return Object.fromEntries(
      userEnrollments.map((enrollment) => [enrollment.course_id, enrollment])
    );
  }, [userEnrollments]);

  return (
    <DashboardLayout>
      <div className="m-6">
        <FadeContent
          blur={true}
          duration={500}
          easing="ease-out"
          initialOpacity={0}
          delay={100}
        >
          <Breadcrumbs
            items={[
              { label: "Inicio", href: "/home", icon: <Home size={16} /> },
              { label: "Cursos", icon: <BookOpen size={16} /> },
            ]}
          />
          <h3 className="text-2xl font-bold text-white">
            Cursos disponibles para ti
          </h3>
        </FadeContent>
        <div className="my-6">
          {/* Pass the derived progressMap to the cards */}
          <CourseCards courses={courses} progressMap={progressMap} />
        </div>
      </div>
    </DashboardLayout>
  );
}
