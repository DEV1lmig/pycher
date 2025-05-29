import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "@tanstack/react-router"; // Added useNavigate
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { getModuleById, getCourseById } from "@/services/contentService"; // getLessonById and getExercisesByLessonId will come from the hook
import LessonCodeExecutor from "@/components/editor/LessonCodeExecutor";
import { LessonWithCodeRoute } from "@/router";
import Waves from "@/components/ui/waves";
import AnimatedContent from "@/components/ui/animated-content";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen, ArrowRight, CheckCircle, Loader2, AlertCircle, BookText } from "lucide-react"; // Added icons
import LessonChatbot from "@/components/ai/LessonChatBot";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useLessonDetail } from '@/hooks/useLessonDetail'; // Import the hook
import { Button } from "@/components/ui/button"; // Import Button
import { toast } from "react-hot-toast";

export default function LessonWithCodePage() {
  const { lessonId: lessonIdParam } = useParams({ from: LessonWithCodeRoute.id });
  const lessonId = parseInt(lessonIdParam);
  const navigate = useNavigate();

  const {
    lesson,
    exercises,
    isLessonCompleted,
    getExerciseProgress,
    loading: lessonDetailLoading,
    error: lessonDetailError,
    submittingExerciseId,
    submitExercise: submitExerciseFromHook,
  } = useLessonDetail(lessonId);

  const [module, setModule] = useState(null);
  const [course, setCourse] = useState(null);
  const [breadcrumbLoading, setBreadcrumbLoading] = useState(true);

  // Determine the current exercise (assuming one main exercise per page for now)
  const currentExercise = exercises && exercises.length > 0 ? exercises[0] : null;
  const currentExerciseProgress = currentExercise ? getExerciseProgress(currentExercise.id) : null;
  const isCurrentExerciseCorrect = currentExerciseProgress?.is_correct || false;

  console.log("Current Exercise:", currentExercise); // <-- ADD THIS LINE

  useEffect(() => {
    if (lesson?.module_id) {
      setBreadcrumbLoading(true);
      getModuleById(lesson.module_id)
        .then(moduleData => {
          setModule(moduleData);
          if (moduleData?.course_id) {
            return getCourseById(moduleData.course_id).then(courseData => {
              setCourse(courseData);
            });
          }
        })
        .catch(err => {
          console.error("Error fetching module/course for breadcrumbs:", err);
          // Optionally set an error state for breadcrumbs
        })
        .finally(() => setBreadcrumbLoading(false));
    } else if (lesson) { // Lesson loaded but no module_id
      setBreadcrumbLoading(false);
    }
  }, [lesson]);

  const handleCodeSubmit = async (codeToSubmit) => { // Renamed param for clarity
    if (!currentExercise) {
      toast.error("No hay ejercicio seleccionado para enviar.");
      return;
    }
    try {
      // submitExerciseFromHook is from useLessonDetail
      const submissionResult = await submitExerciseFromHook(currentExercise.id, codeToSubmit);
      // The hook should handle success/error toasts and state updates
      return submissionResult;
    } catch (error) {
      // Error toast is likely handled by the hook
      console.error("Failed to submit exercise from page:", error);
      // Optionally, re-throw or handle further if needed
    }
  };

  // Placeholder: Logic to find the next lesson ID
  // This would typically involve fetching the current module's lessons and finding the next one by order_index
  const [nextLessonId, setNextLessonId] = useState(null);
  useEffect(() => {
    if (module && lesson) {
      const currentLessonIndex = module.lessons?.findIndex(l => l.id === lesson.id);
      if (module.lessons && currentLessonIndex !== -1 && currentLessonIndex < module.lessons.length - 1) {
        setNextLessonId(module.lessons[currentLessonIndex + 1].id);
      } else {
        setNextLessonId(null); // No more lessons in this module or module.lessons not populated
      }
    }
  }, [module, lesson]);


  if (lessonDetailLoading || (lesson && breadcrumbLoading)) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-white">
          <Loader2 className="h-8 w-8 animate-spin mr-3" />
          Cargando lección...
        </div>
      </DashboardLayout>
    );
  }

  if (lessonDetailError) {
    return (
      <DashboardLayout>
        <div className="flex flex-col justify-center items-center min-h-[40vh] text-lg text-red-400">
          <AlertCircle className="h-12 w-12 mb-4" />
          {lessonDetailError}
        </div>
      </DashboardLayout>
    );
  }

  if (!lesson) {
     return (
      <DashboardLayout>
        <div className="flex flex-col justify-center items-center min-h-[40vh] text-lg text-gray-400">
            <AlertCircle className="h-12 w-12 mb-4" />
            Lección no encontrada o no se pudo cargar.
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
            module && { label: module.title, href: `/module/${module.id}` }, // Ensure module link is correct
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
            <div className="flex justify-between items-start">
                <h1 className="text-3xl font-bold text-white mb-2">{lesson?.title}</h1>
                {isLessonCompleted && (
                    <div className="flex items-center text-green-400 bg-green-900/50 px-3 py-1 rounded-md">
                        <CheckCircle className="h-5 w-5 mr-2" />
                        <span>Lección Completada</span>
                    </div>
                )}
            </div>
            <div className="text-gray-400 mb-4 prose prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{lesson?.description || ""}</ReactMarkdown>
            </div>
          </div>
        </div>
      </AnimatedContent>

      <FadeContent blur={true} duration={300} easing="ease-out" initialOpacity={0} delay={100} >
      <div
        className="grid grid-cols-1 md:grid-cols-2 mx-6 gap-6 custom-scroll"
        style={{ maxHeight: "calc(100vh - 300px)", overflowY: "auto" }} // Adjusted maxHeight
      >
        <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-5 flex flex-col overflow-y-auto custom-scroll">
          <h2 className="font-bold text-lg text-secondary mb-2">{lesson?.title}</h2>
          <hr className="mb-4 border-primary/40" />
          <div className="prose prose-invert max-w-none text-justify flex-grow"> {/* Added flex-grow */}
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{lesson?.content || ""}</ReactMarkdown>
          </div>
          {currentExercise && (
            <div className="mt-6 pt-4 border-t border-primary-opaque/20">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold text-xl text-secondary mb-1">{currentExercise.title}</h3>
                {isCurrentExerciseCorrect && (
                  <div className="flex items-center text-green-400 text-sm">
                    <CheckCircle className="h-4 w-4 mr-1" /> Completado
                  </div>
                )}
              </div>
              <div className="prose prose-invert max-w-none text-gray-300 mb-3">
                 <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentExercise.description || ""}</ReactMarkdown>
              </div>
              {/* Display Exercise Instructions */}
              {currentExercise.instructions && (
                <div className="mt-3 pt-3 border-t border-primary-opaque/10">
                  <h4 className="font-semibold text-md text-secondary mb-2 flex items-center">
                    <BookText size={18} className="mr-2 text-primary" />
                    Instrucciones del Ejercicio:
                  </h4>
                  <div className="prose prose-sm prose-invert max-w-none text-gray-300">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentExercise.instructions}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-3 flex flex-col gap-4">
          {currentExercise ? (
            <LessonCodeExecutor
              key={currentExercise.id}
              initialCode={currentExercise.starter_code || ""}
              exerciseId={currentExercise.id} // Pass exerciseId
              onSubmitCode={handleCodeSubmit} // Pass the submit handler
              isSubmitting={submittingExerciseId === currentExercise.id} // Pass submitting state
              isCorrect={isCurrentExerciseCorrect} // Pass correctness state
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <BookOpen size={48} className="mb-4" />
              <p>Esta lección no tiene un ejercicio interactivo.</p>
            </div>
          )}
        </div>
      </div>
      <div className="mx-6 my-8 flex justify-between">
        <Button variant="outline" onClick={() => navigate({ to: `/module/${lesson?.module_id}` })}>
            Volver al Módulo
        </Button>
        {nextLessonId ? (
            <Button
                onClick={() => navigate({ to: `/lessons/${nextLessonId}` })}
                disabled={!isLessonCompleted}
                variant={isLessonCompleted ? "secondary" : "default"}
            >
                {isLessonCompleted ? "Siguiente Lección" : "Completa la lección"}
                {isLessonCompleted && <ArrowRight className="h-4 w-4 ml-2" />}
            </Button>
        ) : isLessonCompleted && (
             <Button variant="secondary" onClick={() => navigate({ to: `/module/${lesson?.module_id}` })}>
                ¡Módulo Terminado! Volver
            </Button>
        )}
      </div>
    </FadeContent>
      <LessonChatbot lessonId={lessonId} lessonContent={lesson?.content} exercisePrompt={currentExercise?.description} />
    </DashboardLayout>
  );
}
