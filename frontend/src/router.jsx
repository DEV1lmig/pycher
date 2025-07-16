import { createRootRoute, createRouter, createRoute, Outlet } from '@tanstack/react-router';
import { CongratsModalProvider, useCongratsModal } from './context/CongratsModalContext';
import { Toaster } from 'react-hot-toast';
import AllCoursesCompletedModal from './components/modals/AllCoursesCompletedModal';
import LoginPage from '@/pages/auth/LoginPage';
import RegisterPage from '@/pages/auth/RegisterPage';
import LandingPage from '@/pages/LandingPage';
import DashboardPage from '@/pages/home/Dashboard';
import HelpPage from '@/pages/home/help';
import ProfilePage from '@/pages/profile/profile';
import CoursesPage from '@/pages/courses/CoursesPage';
import CourseDetailPage from "./pages/courses/CourseDetailPage";
import ModuleLessonsPage from "./pages/courses/modules/ModuleLessonsPage";
import LessonWithCodePage from "./pages/courses/lessons/LessonWithCodePage";
import { ProtectedLayout } from '@/components/auth/ProtectedLayout'; // Ensure this is correctly imported

function RootLayout() {
  const { isCongratsModalOpen } = useCongratsModal();

  return (
    <>
      <Outlet />
      <Toaster
        position="top-right"
        reverseOrder={false}
        toastOptions={{
          className: 'bg-[#1a1433] text-white border-[#312a56]',
          duration: 3000,
          style: {
            background: '#1a1433',
            color: '#fff',
            border: '1px solid #312a56',
          },
        }}
      />
      {isCongratsModalOpen && <AllCoursesCompletedModal />}
    </>
  );
}

const rootRoute = createRootRoute({
  component: () => (
    <CongratsModalProvider>
      <RootLayout />
    </CongratsModalProvider>
  ),
});

const landingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: LandingPage,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path : '/login',
  component: LoginPage,
});
const registerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path : '/register',
  component: RegisterPage,
});

const protectedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'protected',
  beforeLoad: ProtectedLayout.beforeLoad,
  component: ProtectedLayout.component,
});

const homeRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/home',
  component: DashboardPage,
});

// Renamed for clarity: this is for the list of courses
const coursesListRoute = createRoute({
    getParentRoute: () => protectedRoute,
    path: '/courses', // This path will render CoursesPage
    component: CoursesPage,
});

// Course Detail Page route, now a direct child of protectedRoute
const courseDetailRoute = createRoute({
  getParentRoute: () => protectedRoute, // Parent is now protectedRoute
  path: "/courses/$courseId",          // Full path specified
  component: CourseDetailPage,
});

// Exam Interface Page route, now a direct child of protectedRoute
const examInterfaceRoute = createRoute({
  getParentRoute: () => protectedRoute, // Parent is now protectedRoute
  path: "/courses/$courseId/exam-interface", // Full path specified
  component: LessonWithCodePage,
});

const moduleLessonsRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/module/$moduleId',
  component: ModuleLessonsPage,
});

const lessonWithCodeRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/lessons/$lessonId",
  component: LessonWithCodePage,
});


const helpRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/home/help',
  component: () => <HelpPage />,
})

const ProfileRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/profile',
  component: () => <ProfilePage />,
})

const routeTree = rootRoute.addChildren([
  landingRoute,
  loginRoute,
  registerRoute,
  helpRoute,
  protectedRoute.addChildren([
    homeRoute,
    ProfileRoute,
    coursesListRoute,     // Renders CoursesPage at /courses
    courseDetailRoute,    // Renders CourseDetailPage at /courses/$courseId
    examInterfaceRoute,   // Renders LessonWithCodePage at /courses/$courseId/exam-interface
    moduleLessonsRoute,
    lessonWithCodeRoute,
  ])
]);

const router = createRouter({ routeTree });

export { router, courseDetailRoute, moduleLessonsRoute, lessonWithCodeRoute, examInterfaceRoute, coursesListRoute };
