import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, useMatch } from "@tanstack/react-router"; // Ensure useMatch is imported
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { getModuleById, getCourseById } from "@/services/contentService";
import progressService from "@/services/progressService";
import LessonCodeExecutor from "@/components/editor/LessonCodeExecutor";
import { lessonWithCodeRoute, examInterfaceRoute } from "@/router";
import Waves from "@/components/ui/waves";
import AnimatedContent from "@/components/ui/animated-content";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen, ArrowRightCircle, CheckCircle, Loader2, AlertCircle, BookText, Edit3 } from "lucide-react";
import LessonChatBot from "@/components/ai/LessonChatBot";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useLessonDetail } from '@/hooks/useLessonDetail'; // #useLessonDetail.js
import { getUserProfile } from "@/services/userService"; // 1. Import getUserProfile
import { useCongratsModal } from "@/context/CongratsModalContext"; // <-- 1. IMPORTA EL HOOK
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "react-hot-toast";

export default function LessonWithCodePage() {
  const navigate = useNavigate();
  const { openCongratsModal } = useCongratsModal(); // <-- 2. OBTÉN LA FUNCIÓN DEL HOOK
  const currentRouteMatch = useMatch({});
  const isExamMode = currentRouteMatch?.routeId === examInterfaceRoute.id;

  const params = useParams({
    from: isExamMode ? examInterfaceRoute.id : lessonWithCodeRoute.id,
  });

  const lessonId = !isExamMode ? params.lessonId : undefined;
  const courseIdForExam = isExamMode ? params.courseId : undefined;

  // 2. Add state to hold the user's profile data
  const [user, setUser] = useState(null);

  // 3. Fetch the user profile when the component mounts
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const profileData = await getUserProfile();
        setUser(profileData);
      } catch (error) {
        console.error("Failed to fetch user profile:", error);
        // Optionally, handle the error, e.g., by redirecting to login
      }
    };
    fetchUser();
  }, []); // Empty dependency array means this runs once on mount

  // Lesson detail hook (only used if not in exam mode)
  // This part remains the same, as lessonId will be correctly undefined in exam mode
  const lessonDetailHook = useLessonDetail(lessonId); // #useLessonDetail.js

  // Destructure from hook only if not in exam mode, provide defaults otherwise
  const {
    lesson: lessonDataFromHook,
    exercises: exercisesFromHook,
    isLessonCompleted,
    getExerciseProgress,
    loading: lessonDetailLoading,
    error: lessonDetailError,
    submittingExerciseId,
    submitExercise: submitExerciseFromHook,
    nextLessonInfo,
  } = !isExamMode ? lessonDetailHook : {
    lesson: null, exercises: [], isLessonCompleted: false, getExerciseProgress: () => null,
    loading: false, error: null, submittingExerciseId: null, submitExercise: async () => {}, nextLessonInfo: null
  };

  // State for lesson-specific breadcrumb data
  const [moduleData, setModuleData] = useState(null);
  const [courseData, setCourseData] = useState(null); // For lesson's course
  const [breadcrumbLoading, setBreadcrumbLoading] = useState(!isExamMode);

  // State for exam mode
  const [examCourse, setExamCourse] = useState(null); // Course data for exam breadcrumbs
  const [examExercise, setExamExercise] = useState(null); // The actual exam exercise
  const [examLoading, setExamLoading] = useState(isExamMode);
  const [examError, setExamError] = useState(null);
  const [isExamSubmitting, setIsExamSubmitting] = useState(false);
  const [isExamCorrect, setIsExamCorrect] = useState(null); // null, true, or false for exam pass/fail

  // --- START: ADD THIS NEW STATE ---
  const [lastSubmissionResult, setLastSubmissionResult] = useState(null);
  // --- END: ADD THIS NEW STATE ---

  // Shared state
  const [userStdin, setUserStdin] = useState("");
  const [chatDrawerOpen, setChatDrawerOpen] = useState(false);
  const [courseProgress, setCourseProgress] = useState(null);

  const fetchCourseProgress = useCallback(async () => {
    if (courseData?.id) {
      try {
        const progress = await progressService.getCourseProgressSummary(courseData.id);
        console.log("Fetched course progress:", progress); // <--- LOG HERE
        setCourseProgress(progress);
      } catch (e) {
        // Optionally handle error
      }
    }
  }, [courseData?.id]);

  useEffect(() => {
    fetchCourseProgress();
  }, [fetchCourseProgress]);

  // Fetch lesson-specific breadcrumb data (module and course for the lesson)
  useEffect(() => {
    if (!isExamMode && lessonDataFromHook?.module_id) {
      setBreadcrumbLoading(true);
      getModuleById(lessonDataFromHook.module_id)
        .then(moduleRes => {
          setModuleData(moduleRes); // Used for "Volver al Módulo"
          if (moduleRes?.course_id) {
            return getCourseById(moduleRes.course_id).then(courseRes => {
              setCourseData(courseRes); // Used for lesson breadcrumbs
            });
          }
        })
        .catch(err => {
          // Potentially set an error state for breadcrumbs if critical
        })
        .finally(() => setBreadcrumbLoading(false));
    } else if (!isExamMode && lessonDataFromHook) {
      // If lessonDataFromHook is present but no module_id (should not happen for valid lessons)
      setBreadcrumbLoading(false);
    }
  }, [isExamMode, lessonDataFromHook]);

  // Fetch exam data if in exam mode (course details for breadcrumbs and the exam exercise itself)
  useEffect(() => {
    if (isExamMode && courseIdForExam) {
      setExamLoading(true);
      setExamError(null);
      Promise.all([
        getCourseById(courseIdForExam), // For breadcrumbs
        // --- FIX: Use the imported progressService object ---
        progressService.getCurrentCourseExam(courseIdForExam)
      ]).then(([courseRes, examExerciseRes]) => {
        setExamCourse(courseRes);
        if (examExerciseRes) {
          setExamExercise(examExerciseRes);
        } else {
          setExamError("No se encontró el ejercicio de examen para este curso.");
        }
      }).catch(err => {
        const errorMsg = err.response?.data?.detail || "Error al cargar datos del examen.";
        console.error("Error fetching exam data:", errorMsg, err);
        setExamError(errorMsg);
      }).finally(() => {
        setExamLoading(false);
      });
    }
  }, [isExamMode, courseIdForExam]);

  // Determine the current exercise to be displayed and interacted with
  const currentExercise = isExamMode ? examExercise : (exercisesFromHook && exercisesFromHook.length > 0 ? exercisesFromHook[0] : null);

  useEffect(() => {
    setUserStdin(""); // Reset stdin when exercise changes
  }, [currentExercise?.id]);

  const currentExerciseProgress = !isExamMode && currentExercise && getExerciseProgress
    ? getExerciseProgress(currentExercise.id)
    : null;

  // For lessons, isCurrentExerciseCorrect comes from hook. For exams, we manage it with isExamCorrect state.
  const isCurrentExerciseCorrectForDisplay = isExamMode ? isExamCorrect : (currentExerciseProgress?.is_correct || false);

  const exerciseNeedsInput = !!(
    currentExercise &&
    currentExercise.validation_rules &&
    currentExercise.validation_rules.requires_input_function
  );

  // Handles code submission for both lessons and exams
  const handleCodeSubmit = async (codeToSubmit) => {
    if (!currentExercise) {
      toast.error("No hay ejercicio seleccionado para enviar.");
      return;
    }
    setLastSubmissionResult(null);

    if (isExamMode) { // Exam Submission Logic
      setIsExamSubmitting(true);
      setIsExamCorrect(null);
      try {
        const submissionResult = await progressService.submitExercise(currentExercise.id, codeToSubmit, userStdin);

        // --- 3. MODIFICA LA LÓGICA DE ÉXITO ---
        if (submissionResult?.is_correct) {
          // Comprueba si la bandera especial viene en la respuesta
          if (submissionResult?.validation_result?.all_courses_completed) {
            // Si es así, abre el modal de felicitación final
            openCongratsModal(); // Open the modal
          } else {
            // Si no, es solo un examen normal aprobado, muestra un toast
            toast.success(`Examen "${currentExercise.title}" enviado. ¡Resultado Correcto!`);
          }
        } else {
          // Show a detailed error toast
          toast.error(submissionResult.validation_result?.error || "Resultado: Incorrecto");
        }
        // --- END: IMPROVED TOAST AND RESULT HANDLING ---

        setIsExamCorrect(submissionResult.is_correct);
        // --- FIX: Pass the nested validation_result to the executor ---
        setLastSubmissionResult(submissionResult.validation_result);
        return submissionResult;
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || "Error al enviar el examen.";
        toast.error(errorMsg);
        setLastSubmissionResult({ error: errorMsg, passed: false, output: "" });
        setIsExamCorrect(false);
      } finally {
        setIsExamSubmitting(false);
      }
    } else { // Lesson Exercise Submission Logic (uses hook)
      try {
        // --- FIX: Pass disableToast option to the hook ---
        const submissionResult = await submitExerciseFromHook(
          currentExercise.id,
          codeToSubmit,
          userStdin,
          { disableToast: true } // This prevents the hook from showing a toast
        );

        // This component's toast logic will now be the only one running
        if (submissionResult.is_correct) {
          toast.success("¡Ejercicio correcto!");
          await fetchCourseProgress();
        } else {
          toast.error(submissionResult.validation_result?.error || "Resultado: Incorrecto. Revisa la salida.");
        }

        setLastSubmissionResult(submissionResult.validation_result);
        return submissionResult;
      } catch (error) {
        // This catch block will now only handle errors if the API call itself fails
        // The hook no longer shows a toast, so we can add one here if needed,
        // but the component's logic above already covers most cases.
        setLastSubmissionResult({ error: error.message, passed: false, output: "" });
      }
    }
  };

  // Determine overall loading state and error for the page
  const isLoading = isExamMode ? examLoading : (lessonDetailLoading || (lessonDataFromHook && breadcrumbLoading));
  const pageError = isExamMode ? examError : lessonDetailError;
  const pageData = isExamMode ? examExercise : lessonDataFromHook; // Primary data object (exam or lesson)

  // Loading, Error, and No Data states
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-white">
          <Loader2 className="h-8 w-8 animate-spin mr-3" />
          Cargando {isExamMode ? "examen" : "lección"}...
        </div>
      </DashboardLayout>
    );
  }

  if (pageError) {
    return (
      <DashboardLayout>
        <div className="flex flex-col justify-center items-center min-h-[40vh] text-lg text-red-400 p-4 text-center">
          <AlertCircle className="h-12 w-12 mb-4" />
          {pageError}
        </div>
      </DashboardLayout>
    );
  }

  if (!pageData) {
    return (
      <DashboardLayout>
        <div className="flex flex-col justify-center items-center min-h-[40vh] text-lg text-gray-400 p-4 text-center">
          <AlertCircle className="h-12 w-12 mb-4" />
          {isExamMode ? "Examen no encontrado." : "Lección no encontrada o no se pudo cargar."}
        </div>
      </DashboardLayout>
    );
  }

  // Construct breadcrumbs based on mode
  const breadcrumbs = [
    { label: "Inicio", href: "/home", icon: <Home size={16} /> },
    { label: "Cursos", href: "/courses", icon: <BookOpen size={16} /> },
  ];
  if (isExamMode) {
    if (examCourse) breadcrumbs.push({ label: examCourse.title, href: `/courses/${examCourse.id}` });
    breadcrumbs.push({ label: examExercise?.title || "Examen Final", icon: <Edit3 size={16} /> });
  } else {
    if (courseData) breadcrumbs.push({ label: courseData.title, href: `/courses/${courseData.id}` });
    if (moduleData) breadcrumbs.push({ label: moduleData.title, href: `/module/${moduleData.id}` });
    if (lessonDataFromHook) breadcrumbs.push({ label: lessonDataFromHook.title });
  }

  // UI content variables based on mode
  const pageTitle = isExamMode ? (examExercise?.title || "Examen Final") : lessonDataFromHook?.title;
  const pageDescription = isExamMode ? (examExercise?.description || "") : (lessonDataFromHook?.description || "");
  const mainContent = isExamMode ? (examExercise?.instructions || "") : (lessonDataFromHook?.content || ""); // Exam instructions are the main content
  const chatContextContent = isExamMode ? (examExercise?.instructions || examExercise?.description) : lessonDataFromHook?.content;

  return (
    <DashboardLayout>
      <div className="my-4 mx-6">
        <Breadcrumbs items={breadcrumbs.filter(Boolean)} />
      </div>
      <AnimatedContent distance={40} direction="vertical" reverse={true} config={{ tension: 100, friction: 20 }} initialOpacity={0.2} animateOpacity scale={1} threshold={0.2} >
        <div className="relative rounded-lg p-8 mx-6 my-6 shadow-2xl border border-primary-opaque/0">
          <div className="absolute rounded-3xl overflow-hidden inset-0 z-10">
            <Waves lineColor="rgba(152, 128, 242, 0.4)" backgroundColor="#160f30" waveSpeedX={0.02} waveSpeedY={0.01} waveAmpX={70} waveAmpY={20} friction={0.9} tension={0.01} maxCursorMove={60} xGap={12} yGap={36} />
          </div>
          <div className="relative z-20">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">{pageTitle}</h1>
                <div className="text-gray-400 mb-4 prose prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{pageDescription}</ReactMarkdown>
                </div>
              </div>
              {/* Conditional UI for lesson completion / exam status */}
              <div className="flex flex-col md:items-end md:justify-end gap-2">
                {!isExamMode && isLessonCompleted && (
                  <div className="flex items-center text-green-400 bg-green-900/50 px-3 py-1 rounded-md mb-1 md:mb-0">
                    <CheckCircle className="h-5 w-5 mr-2" />
                    <span>Lección Completada</span>
                  </div>
                )}
                {!isExamMode && isLessonCompleted && nextLessonInfo && (
                  <Button onClick={() => { if (nextLessonInfo?.id) navigate({ to: `/lessons/$lessonId`, params: { lessonId: nextLessonInfo.id.toString() } }); else toast.error("No se pudo determinar la siguiente lección."); }} className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg text-base mt-2 md:mt-0" size="lg" >
                    <ArrowRightCircle className="mr-2 h-5 w-5" />
                    Siguiente Lección: {nextLessonInfo.title || "Siguiente"}
                  </Button>
                )}
                {!isExamMode && isLessonCompleted && !nextLessonInfo && (
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg shadow-md text-center text-blue-700 dark:text-blue-300 mt-2 md:mt-0">
                    ¡Has completado todas las lecciones de este módulo!
                    <Button variant="secondary" className="ml-3" onClick={() => navigate({ to: `/courses/${courseData?.id || lessonDataFromHook?.module?.course_id || ''}` })}>
                      Volver al Curso
                    </Button>
                  </div>
                )}
                {isExamMode && isExamCorrect === true && ( // Exam Passed
                  <div className="flex items-center text-green-400 bg-green-900/50 px-3 py-1 rounded-md mb-1 md:mb-0">
                    <CheckCircle className="h-5 w-5 mr-2" />
                    <span>Examen Aprobado</span>
                  </div>
                )}
                {isExamMode && isExamCorrect === false && ( // Exam Failed
                  <div className="flex items-center text-red-400 bg-red-900/50 px-3 py-1 rounded-md mb-1 md:mb-0">
                    <AlertCircle className="h-5 w-5 mr-2" />
                    <span>Examen No Aprobado. Inténtalo de nuevo.</span>
                  </div>
                )}
                <Button
                  variant="outline"
                  className="mt-2"
                  onClick={() => {
                    if (isExamMode) {
                      navigate({ to: `/courses/${courseIdForExam}` });
                    } else {
                      const targetModuleId = moduleData?.id || lessonDataFromHook?.module_id;
                      if (targetModuleId) {
                        navigate({ to: `/module/${targetModuleId}` });
                      } else {
                        toast.error("No se pudo determinar el módulo para volver.");
                        navigate({ to: `/courses` });
                      }
                    }
                  }}
                >
                  {isExamMode ? "Volver al Curso" : "Volver al Módulo"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </AnimatedContent>

      <FadeContent blur={true} duration={300} easing="ease-out" initialOpacity={0} delay={100}>
        <div
          className={`grid gap-6 mx-6 custom-scroll transition-all duration-300 ${
            chatDrawerOpen
              ? "grid-cols-1 md:grid-cols-2 xl:grid-cols-3"
              : "grid-cols-1 md:grid-cols-2"
          }`}
          style={{ height: "calc(100vh - 300px)" }}
        >
          {/* Content/Instructions Column */}
          <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-5 flex flex-col overflow-y-auto custom-scroll flex-1" style={{ maxHeight: "calc(100vh - 300px)" }}>
            <h2 className="font-bold text-lg text-secondary mb-2">
              {isExamMode ? "Consigna del Examen" : "Contenido de la Lección"}
            </h2>
            <hr className="mb-4 border-primary/40" />
            <div className="prose prose-invert max-w-none text-justify flex-grow">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{mainContent}</ReactMarkdown>
            </div>
            {/* Lesson-specific exercise details (hidden in exam mode) */}
            {!isExamMode && currentExercise && (
              <div className="mt-6 pt-4 border-t border-primary-opaque/20">
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold text-xl text-secondary mb-1">
                    {currentExercise.title}
                  </h3>
                  {isCurrentExerciseCorrectForDisplay && (
                    <div className="flex items-center text-green-400 text-sm">
                      <CheckCircle className="h-4 w-4 mr-1" /> Completado
                    </div>
                  )}
                </div>
                <div className="prose prose-invert max-w-none text-gray-300 mb-3">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentExercise.description || ""}</ReactMarkdown>
                </div>
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
          {/* Code Editor Column */}
          <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-3 flex flex-col flex-1 overflow-y-auto custom-scroll" style={{ maxHeight: "calc(100vh - 300px)" }}>
            {currentExercise ? (
              <>
                <LessonCodeExecutor
                  key={currentExercise.id}
                  initialCode={currentExercise.starter_code || ""}
                  exerciseId={currentExercise.id}
                  onSubmitCode={handleCodeSubmit}
                  isSubmitting={isExamMode ? isExamSubmitting : (submittingExerciseId === currentExercise.id)}
                  isCorrect={isCurrentExerciseCorrectForDisplay}
                  currentUserStdin={userStdin}
                  // --- START: PASS THE SUBMISSION RESULT ---
                  submissionResult={lastSubmissionResult}
                  // --- END: PASS THE SUBMISSION RESULT ---
                />
                {exerciseNeedsInput && (
                  <div className="mt-2">
                    <label htmlFor="user-stdin" className="block text-sm font-medium text-gray-300 mb-1">
                      Entrada estándar (para <code>input()</code>):
                    </label>
                    <Textarea id="user-stdin" value={userStdin} onChange={(e) => setUserStdin(e.target.value)} placeholder="Escribe aquí la entrada que tu código leerá con input()..." className="bg-primary-opaque/70 border-primary-opaque/30 text-sm" rows={3} />
                  </div>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <BookOpen size={48} className="mb-4" />
                <p>
                  {isExamMode
                    ? "No se pudo cargar el ejercicio de examen."
                    : "Esta lección no tiene un ejercicio interactivo."}
                </p>
              </div>
            )}
            <Button
              className="mt-4 self-end"
              variant="secondary"
              onClick={() => setChatDrawerOpen(true)}
            >
              💬 Abrir Chat IA
            </Button>
          </div>

          {/* Chat Sidebar */}
          {chatDrawerOpen && (
            <aside className="h-full min-h-0 flex flex-col xl:col-span-1 col-span-full">
              <LessonChatBot
                onClose={() => setChatDrawerOpen(false)}
                lessonContext={chatContextContent}
                starterCode={currentExercise?.starter_code || ""}
                // 4. Pass the user ID from the state
                userId={user?.id}
                lessonId={lessonId}
              />
            </aside>
          )}
        </div>
      </FadeContent>
      {courseProgress?.is_course_completed && !isExamMode && (
  <>
    {console.log("Rendering 'Curso completado' message. courseProgress:", courseProgress)} {/* <--- LOG HERE */}
    <div className="p-3 bg-green-50 border border-green-200 rounded-lg shadow-md text-center text-green-700 mt-2">
      ¡Curso completado!
    </div>
  </>
)}
    </DashboardLayout>
  );
}
