import { createRootRoute, createRouter, createRoute,  } from '@tanstack/react-router'
import DemoPage from './pages/DemoPage'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/home/Dashboard';
import CoursesPage from './pages/courses/CoursesPage'
import { ProtectedLayout } from './components/auth/ProtectedLayout';
import CourseDetailPage from './pages/courses/CourseDetailPage';

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

const moduleRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/module/$moduleId',
  component: ({ params }) => <div>Module {params.moduleId}</div>,
})

const editorRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/editor/$exerciseId',
  component: ({ params }) => <div>Code Editor {params.exerciseId}</div>,
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

const demoRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/demo',
  component: () => <DemoPage />,
})

// Create the route tree using your routes
const routeTree = rootRoute.addChildren([
  landingRoute,
  moduleRoute,
  editorRoute,
  demoRoute,
  loginRoute,
  registerRoute,
  protectedRoute.addChildren([homeRoute, coursesRoute, courseDetailRoute])
])

// Create the router using your route tree
export { courseDetailRoute }; // <-- Add this line

export const router = createRouter({ routeTree })
