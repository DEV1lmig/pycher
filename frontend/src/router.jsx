import { createRootRoute, createRouter, createRoute } from '@tanstack/react-router'
import DemoPage from './pages/DemoPage'
import HomePage from './pages/HomePage'

const rootRoute = createRootRoute()

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => <HomePage />,
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
  indexRoute,
  moduleRoute,
  editorRoute,
  demoRoute,
])

// Create the router using your route tree
export const router = createRouter({ routeTree })
