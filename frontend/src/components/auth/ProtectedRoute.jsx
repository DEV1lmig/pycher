import { Navigate } from '@tanstack/react-router';
import { isAuthenticated } from '@/lib/auth';

export default function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }
  return children;
}
