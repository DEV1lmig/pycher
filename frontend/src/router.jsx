import { createRootRoute, createRouter, createRoute } from '@tanstack/react-router';
import LoginPage from '@/pages/auth/LoginPage';
import RegisterPage from '@/pages/auth/RegisterPage';
import LandingPage from '@/pages/LandingPage';
import DashboardPage from '@/pages/home/Dashboard';
/* import HelpPage from '@/pages/home/HelpPage';
import ProfilePage from '@/pages/profile/ProfilePage'; */
import CoursesPage from '@/pages/courses/CoursesPage';
import CourseDetailPage from "./pages/courses/CourseDetailPage";
import ModuleLessonsPage from "./pages/courses/modules/ModuleLessonsPage";
import LessonWithCodePage from "./pages/courses/lessons/LessonWithCodePage";
import { ProtectedLayout } from '@/components/auth/ProtectedLayout'; // Ensure this is correctly imported

const rootRoute = createRootRoute();

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
  protectedRoute.addChildren([
    homeRoute,
    ProfileRoute, // Added ProfileRoute under protectedRoute
    helpRoute,
    coursesListRoute,     // Renders CoursesPage at /courses
    courseDetailRoute,    // Renders CourseDetailPage at /courses/$courseId
    examInterfaceRoute,   // Renders LessonWithCodePage at /courses/$courseId/exam-interface
    moduleLessonsRoute,
    lessonWithCodeRoute,
  ])
]);

const router = createRouter({ routeTree });

export { router, courseDetailRoute, moduleLessonsRoute, lessonWithCodeRoute, examInterfaceRoute, coursesListRoute }; // Added coursesListRoute
