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
import HelpPage from './pages/home/help'
import ProfilePage from './pages/profile/profile'

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

const helpRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/home/help',
  component: () => <HelpPage />,
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

const LessonWithCodeRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/lessons/$lessonId',
  component: () => <LessonWithCodePage />,
});

const moduleLessonsRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/module/$moduleId',
  component: () => <ModuleLessonsPage />,
})

const ProfileRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/profile',
  component: () => <ProfilePage />,
})

// Create the route tree using your routes
const routeTree = rootRoute.addChildren([
  landingRoute,
  loginRoute,
  registerRoute,
  ProfileRoute,
  protectedRoute.addChildren([
    homeRoute,
    helpRoute,
    coursesRoute,
    courseDetailRoute,
    LessonWithCodeRoute,
    moduleLessonsRoute,
  ])
])

const router = createRouter({ routeTree })

export { router, courseDetailRoute, LessonWithCodePage, moduleLessonsRoute, LessonWithCodeRoute };
