import { useEffect, useState } from "react";
import { CourseCards } from "@/components/dashboard/CourseCards";
import { getAllCourses } from "@/services/contentService";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen } from "lucide-react";

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    getAllCourses().then(setCourses);
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
          <CourseCards courses={courses} />
        </div>
      </div>
    </DashboardLayout>
  );
}