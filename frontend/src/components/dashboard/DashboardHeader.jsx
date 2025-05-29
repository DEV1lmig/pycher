"use client"

import { useEffect, useState } from "react";
import { User, HelpCircle, LogOut, ChevronDown } from "lucide-react" // Removed Bell
// Removed SearchBar import
import { getUserProfile } from "@/services/userService";
import { Link, useNavigate } from '@tanstack/react-router';
import { logout } from "@/lib/auth";
import logo from "@/assets/img/logo-pycher.png"

export function DashboardHeader() {
  // Removed showNotifications state
  const [showProfile, setShowProfile] = useState(false)
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    getUserProfile().then(setUser);
  }, []);

    const handleLogout = () => {
      logout();
      navigate({ to: "/login" });
    };

  return (
    <header className="bg-[#1a1433] border-b border-[#312a56] p-4 flex items-center justify-between">
      <Link to="/home" className="w-36 h-auto cursor-pointer">
        <img src={logo} alt="logo" className="w-36 h-auto hover:scale-105 duration-300 transition-all" />
      </Link>
      {/* SearchBar component removed */}

      <div className="flex items-center space-x-4 ml-auto"> {/* Added ml-auto to push profile to the right */}
        {/* Notifications button and dropdown removed */}

        <div className="relative">
          <button
          onClick={() => setShowProfile(!showProfile)}
          className="flex items-center space-x-2 p-2 rounded-md hover:bg-[#312a56] "
        >
          <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
            <User className="h-5 w-5 text-white" />
          </div>
          <span className="hidden md:inline-block">
            {user ? `${user.first_name} ${user.last_name}` : "Carlos Rodríguez"}
          </span>
          <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${showProfile ? "rotate-180" : ""}`} />
        </button>

          {showProfile && (
          <div className="absolute right-0 mt-2 w-56 bg-[#1a1433] border border-[#312a56] rounded-md shadow-lg z-10">
            <div className="p-3 border-b border-[#312a56]">
              <p className="font-medium">{user ? `${user.first_name} ${user.last_name}` : "Carlos Rodríguez"}</p>
              <p className="text-xs text-gray-400">{user ? user.email : "carlos@example.com"}</p>
            </div>
            <ul>
              <li>
                <Link
                  to="/profile"
                  className="flex items-center gap-2 p-2 hover:bg-[#312a56] cursor-pointer w-full text-base font-semibold hover:text-white"
                >
                  <User className="h-5 w-5 text-[#9980f2]" />
                  Mi Perfil
                </Link>
              </li>
              <li>
                <Link
                  to="/home/help"
                  className="flex items-center gap-2 p-2 hover:bg-[#312a56] cursor-pointer w-full text-base font-semibold hover:text-white"
                >
                  <HelpCircle className="h-5 w-5 text-[#9980f2]" />
                  FAQ
                </Link>
              </li>
              <li>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 p-2 cursor-pointer w-full text-base font-semibold text-left border-t border-[#312a56] hover:text-red/70"
                >
                  <LogOut className="h-5 w-5 text-red/70" />
                  Cerrar Sesión
                </button>
              </li>
            </ul>
          </div>
        )}
        </div>
      </div>
    </header>
  )
}
