// src/pages/auth/ProtectedLayout.jsx
import { Outlet, redirect } from '@tanstack/react-router'
import { isAuthenticated } from '@/lib/auth'

export const ProtectedLayout = {
  beforeLoad: async ({ location }) => {
    try {
      if (!isAuthenticated()) {
        throw redirect({
          to: '/login',
          search: {
            redirect: location.href,
          },
        })
      }
    } catch (error) {
      // If there's any error in auth check, redirect to login
      throw redirect({
        to: '/login',
        search: {
          redirect: location.href,
        },
      })
    }
  },
  component: Outlet,
}
