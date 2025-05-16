import { createRootRoute, createRouter, createRoute,  } from '@tanstack/react-router'
import DemoPage from '@/pages/DemoPage'
import LoginPage from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'
import LandingPage from '@/pages/LandingPage'
import DashboardPage from '@/pages/home/Dashboard';
import CoursesPage from '@/pages/courses/CoursesPage'
import CourseDetailPage from '@/pages/courses/CourseDetailPage';
import LessonWithCodePage from '@/pages/courses/lessons/LessonWithCodePage';
import { ProtectedLayout } from '@/components/auth/ProtectedLayout';
import ModuleLessonsPage from '@/pages/courses/modules/ModuleLessonsPage';

const rootRoute = createRootRoute()

const landingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => <LandingPage />,
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path : '/login',
  component: () => <LoginPage />,
})
const registerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path : '/register',
  component: () => <RegisterPage />,
})

const protectedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'protected',
  path: '',
  beforeLoad: ProtectedLayout.beforeLoad,
  component: ProtectedLayout.component,
})

const homeRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/home',
  component: () => <DashboardPage />,
})

const coursesRoute = createRoute({
    getParentRoute: () => protectedRoute,
    path: '/courses',
    component: () => <CoursesPage />,
})

const courseDetailRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/courses/$courseId',
  component: () => <CourseDetailPage />,
});

const LessonsWithCodeRoute = createRoute({
  getParentRoute: () => moduleLessonsRoute,
  path: '/lessons/$lessonId',
  component: () => <LessonsWithCodePage />,
});

const demoRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/demo',
  component: () => <DemoPage />,
})

const moduleLessonsRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/module/$moduleId',
  component: () => <ModuleLessonsPage />,
})

// Create the route tree using your routes
const routeTree = rootRoute.addChildren([
  landingRoute,
  demoRoute,
  loginRoute,
  registerRoute,
  protectedRoute.addChildren([
    homeRoute,
    coursesRoute,
    courseDetailRoute,
    LessonsWithCodeRoute,
    moduleLessonsRoute,
  ])
])

const router = createRouter({ routeTree })

export { router, courseDetailRoute, LessonWithCodePage, moduleLessonsRoute, LessonsWithCodeRoute };
