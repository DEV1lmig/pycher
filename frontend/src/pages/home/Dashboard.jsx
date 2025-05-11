import DashboardLayout from "@/components/dashboard/DashboardLayout"
import { useEffect, useState } from "react"
import { CourseCards } from "@/components/dashboard/CourseCards"
import { WelcomeHeader } from "@/components/dashboard/WelcomeHeader"
import { StatsCards } from "@/components/dashboard/StatsCards"
import { getAllCourses } from "@/services/contentService"

export default function DashboardPage() {
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    getAllCourses().then(setCourses);
  }, []);
  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6 p-6">
        <WelcomeHeader />
        <StatsCards />
        <section>
          <h2 className="text-2xl font-bold text-white mb-4">Nuestros Cursos</h2>
          <p className="text-gray-300 mb-6">
            Selecciona el curso que deseas estudiar y comienza tu viaje en el mundo de Python
          </p>
          <CourseCards courses={courses} />
        </section>
      </div>
    </DashboardLayout>
  )
}
