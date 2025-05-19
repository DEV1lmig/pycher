import { useEffect, useState } from "react";
import { CourseCards } from "@/components/dashboard/CourseCards";
import { getAllCourses } from "@/services/contentService";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import SplitText from "../../components/ui/split-text";

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);
  const handleAnimationComplete = () => {
    console.log('All letters have animated!');
  };

  useEffect(() => {
    getAllCourses().then(setCourses);
  }, []);

  return (
    <DashboardLayout>
      <div className="m-6">
      <SplitText
        text="Cursos disponibles para ti" 
        className="text-2xl font-bold text-white"
        delay={20}
        animationFrom={{ opacity: 0, transform: 'translate3d(0,0,0)' }}
        animationTo={{ opacity: 1, transform: 'translate3d(0,0,0)' }}
        easing="easeInOutCubic"
        threshold={0}
        rootMargin="-100px"
        onLetterAnimationComplete={handleAnimationComplete}
      />
      <div className="my-6"><CourseCards courses={courses} /></div>
      </div>
    </DashboardLayout>
  );
}
