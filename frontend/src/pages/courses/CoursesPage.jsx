import { useEffect, useState } from "react";
import { CourseCards } from "@/components/dashboard/CourseCards";
import { getAllCourses } from "@/services/contentService";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import FadeContent from "@/components/ui/fade-content";

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    getAllCourses().then(setCourses);
  }, []);

  return (
    <DashboardLayout>
      <div className="m-6">
      <FadeContent blur={true} duration={200} easing="ease-out" initialOpacity={0} delay={200} >
      <h3 className="text-2xl font-bold text-white mx-6">Cursos disponibles para ti</h3>
      </FadeContent>

      <div className="my-6"><CourseCards courses={courses} /></div>
      </div>
    </DashboardLayout>
  );
}
