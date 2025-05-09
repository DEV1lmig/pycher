import { createRootRoute, createRouter, createRoute,  } from '@tanstack/react-router'
import DemoPage from './pages/DemoPage'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/home/Dashboard';
import { ProtectedLayout } from './components/auth/ProtectedLayout';

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

// Add this new route
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
  protectedRoute.addChildren([homeRoute])
])

// Create the router using your route tree
export const router = createRouter({ routeTree })
