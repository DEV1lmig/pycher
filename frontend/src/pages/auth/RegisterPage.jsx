import { useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { isAuthenticated } from "@/lib/auth";
import AuthLayout from "@/components/auth/AuthLayout";

export default function RegisterPage() {
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated()) {
      navigate({ to: "/home" }); // or your home route
    }
  }, []);
  return <AuthLayout />;
}
