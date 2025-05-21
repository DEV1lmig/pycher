import { useEffect, useState } from "react";
import { useParams, Link } from "@tanstack/react-router";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { getLessonById, getExercisesByLessonId, getModuleById, getCourseById } from "@/services/contentService";
import LessonCodeExecutor from "@/components/editor/LessonCodeExecutor";
import { LessonWithCodeRoute } from "@/router";
import Waves from "@/components/ui/waves";
import AnimatedContent from "@/components/ui/animated-content";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen } from "lucide-react";
import LessonChatbot from "@/components/ai/LessonChatbot";

export default function LessonWithCodePage() {
  const { lessonId } = useParams({ from: LessonWithCodeRoute.id });
  const [lesson, setLesson] = useState(null);
  const [module, setModule] = useState(null);
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lessonError, setLessonError] = useState(null);

  // Add exercise state
  const [exercise, setExercise] = useState(null);
  const [initialCode, setInitialCode] = useState("");

  useEffect(() => {
    setLoading(true);
    setLessonError(null);

    // Fetch lesson, then module, then course
    getLessonById(lessonId)
      .then(lessonData => {
        setLesson(lessonData);
        if (lessonData?.module_id) {
          return getModuleById(lessonData.module_id).then(moduleData => {
            setModule(moduleData);
            if (moduleData?.course_id) {
              return getCourseById(moduleData.course_id).then(courseData => {
                setCourse(courseData);
              });
            }
          });
        }
      })
      .catch(err => setLessonError(err.message));

    // Fetch exercise(s)
    getExercisesByLessonId(lessonId)
      .then(exercises => {
        if (exercises && exercises.length > 0) {
          setExercise(exercises[0]);
          setInitialCode(exercises[0].starter_code || "");
        } else {
          setExercise(null);
          setInitialCode("");
        }
      })
      .catch(() => { /* ignore for now */ })
      .finally(() => setLoading(false));
  }, [lessonId]);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-white">
          Cargando lección...
        </div>
      </DashboardLayout>
    );
  }

  if (lessonError) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-red-400">
          {lessonError}
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="my-4 mx-6">
        <Breadcrumbs
          items={[
            { label: "Inicio", href: "/home", icon: <Home size={16} /> },
            { label: "Cursos", href: "/courses", icon: <BookOpen size={16} /> },
            course && { label: course.title, href: `/courses/${course.id}` },
            module && { label: module.title, href: `/module/${module.id}` },
            lesson && { label: lesson.title },
          ].filter(Boolean)}
        />
      </div>
      <AnimatedContent
        distance={40}
        direction="vertical"
        reverse={true}
        config={{ tension: 100, friction: 20 }}
        initialOpacity={0.2}
        animateOpacity
        scale={1}
        threshold={0.2}
      >
        <div className="relative rounded-lg p-8 mx-6 my-6 shadow-2xl border border-primary-opaque/0">
          <div className="absolute rounded-3xl overflow-hidden inset-0 z-10">
            <Waves
              lineColor="rgba(152, 128, 242, 0.4)"
              backgroundColor="#160f30"
              waveSpeedX={0.02}
              waveSpeedY={0.01}
              waveAmpX={70}
              waveAmpY={20}
              friction={0.9}
              tension={0.01}
              maxCursorMove={60}
              xGap={12}
              yGap={36}
            />
          </div>
          <div className="relative z-20">
            <h1 className="text-3xl font-bold text-white mb-2">{lesson?.title}</h1>
            <p className="text-gray-400 mb-4">{lesson?.description || ""}</p>
          </div>
        </div>
      </AnimatedContent>

      <FadeContent blur={true} duration={300} easing="ease-out" initialOpacity={0} delay={100} >
      <div
        className="grid grid-cols-1 md:grid-cols-2 mx-6 gap-6 custom-scroll"
        style={{ maxHeight: "580px", overflowY: "auto" }}
      >
        {/* Lesson Content Card */}
        <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-5 flex flex-col">
          <h2 className="font-bold text-lg text-secondary mb-2">{lesson?.title}</h2>
          <hr className="mb-4 border-primary/40" />
          <div className="prose text-justify max-w-none text-gray-200 whitespace-pre-line">
            {lesson?.content}
          </div>
          {exercise && (
            <>
              <h3 className="font-semibold text-lg text-secondary mt-6">{exercise.title}</h3>
              <div className="text-gray-300">{exercise.description}</div>
            </>
          )}
        </div>
        {/* Code Editor Card */}
        <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-3 flex flex-col gap-4">
          <LessonCodeExecutor initialCode={initialCode} />
        </div>
      </div>
    </FadeContent>
      <LessonChatbot />
    </DashboardLayout>
  );
}
