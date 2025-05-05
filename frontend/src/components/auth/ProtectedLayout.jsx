// src/pages/auth/ProtectedLayout.jsx
import { Outlet, redirect } from '@tanstack/react-router'
import { isAuthenticated } from '@/lib/auth'

export const ProtectedLayout = {
  beforeLoad: () => {
    if (!isAuthenticated()) {
      throw redirect({ to: '/login' })
    }
  },
  component: Outlet,
}
