import DashboardLayout from "@/components/dashboard/DashboardLayout"
import { useEffect, useState } from "react"
import { CourseCards } from "@/components/dashboard/CourseCards"
import { WelcomeHeader } from "@/components/dashboard/WelcomeHeader"
import { StatsCards } from "@/components/dashboard/StatsCards"
import { getAllCourses } from "@/services/contentService"
import FadeContent from "../../components/ui/fade-content.jsx"
import { getCompletedExercisesCount } from "@/services/progressService.js"

export default function DashboardPage() {
  const [courses, setCourses] = useState([]);
  const [completedExercisesCount, setCompletedExercisesCount] = useState(0);

  useEffect(() => {
    getAllCourses().then(async (coursesData) => {
        coursesData.sort((a, b) => a.id - b.id);
        setCourses(coursesData);
    getCompletedExercisesCount().then(async (count) => {
        if (count !== undefined && count !== null) {
          setCompletedExercisesCount(count);
        }
        else {
          setCompletedExercisesCount(0);
        }
    })
    });
  }, []);
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
          <CourseCards courses={courses} />

        </section>
      </div>
    </DashboardLayout>
  )
}
