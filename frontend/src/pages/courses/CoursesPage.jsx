import { useEffect, useState } from "react";
import { CourseCards } from "@/components/dashboard/CourseCards";
import { getAllCourses } from "@/services/contentService";
import DashboardLayout from "@/components/dashboard/DashboardLayout";

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    getAllCourses().then(setCourses);
  }, []);

  return (
    <DashboardLayout>
      <h2 className="text-2xl font-bold text-white mb-4">Cursos Disponibles</h2>
      <CourseCards courses={courses} />
    </DashboardLayout>
  );
}
