import { Link, useLocation } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function AuthTabs() {
  const pathname = useLocation({ select: (location) => location.pathname });

  return (
    <div className="grid grid-cols-2 gap-4">
      <Link to="/login" className="w-full">
        <Button
          variant="outline"
          className={cn(
            "w-full rounded-md border-[#312a56] bg-[#1a1433] text-white hover:bg-[#312a56] hover:text-white",
            pathname === "/login" && "border-t-2 border-t-[#5f2dee]"
          )}
        >
          Inicio de Sesión
        </Button>
      </Link>
      <Link to="/register" className="w-full">
        <Button
          variant="outline"
          className={cn(
            "w-full rounded-md border-[#312a56] bg-[#1a1433] text-white hover:bg-[#312a56] hover:text-white",
            pathname === "/register" && "border-t-2 border-t-[#5f2dee]"
          )}
        >
          Registrarse
        </Button>
      </Link>
    </div>
  );
}