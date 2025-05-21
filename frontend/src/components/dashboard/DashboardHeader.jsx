"use client"

import { useEffect, useState } from "react";
import { Bell, User, HelpCircle, LogOut } from "lucide-react"
import { SearchBar } from "@/components/modules/SearchBar"
import { getUserProfile } from "@/services/userService";
import { Link, useNavigate } from '@tanstack/react-router';
import { logout } from "@/lib/auth";
import logo from "@/assets/img/logo-pycher.png"

export function DashboardHeader() {
  const [showNotifications, setShowNotifications] = useState(false)
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
      <SearchBar />
      
      <div className="flex items-center space-x-4">
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-full hover:bg-[#312a56] relative"
          >
            <Bell className="h-5 w-5 text-gray-300" />
            <span className="absolute top-0 right-0 h-2 w-2 bg-[#f2d231] rounded-full"></span>
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-[#1a1433] border border-[#312a56] rounded-md shadow-lg z-10">
              <div className="p-3 border-b border-[#312a56]">
                <h3 className="font-medium">Notificaciones</h3>
              </div>
              <div className="max-h-96 overflow-y-auto">
                <div className="p-3 border-b border-[#312a56] hover:bg-[#312a56] cursor-pointer">
                  <p className="text-sm font-medium">Nuevo curso disponible</p>
                  <p className="text-xs text-gray-400">Python para Ciencia de Datos ya está disponible</p>
                  <p className="text-xs text-gray-500 mt-1">Hace 2 horas</p>
                </div>
                <div className="p-3 border-b border-[#312a56] hover:bg-[#312a56] cursor-pointer">
                  <p className="text-sm font-medium">Recordatorio</p>
                  <p className="text-xs text-gray-400">No olvides completar tu ejercicio semanal</p>
                  <p className="text-xs text-gray-500 mt-1">Hace 1 día</p>
                </div>
              </div>
              <div className="p-2 text-center">
                <button className="text-sm text-[#9980f2] hover:underline">Ver todas</button>
              </div>
            </div>
          )}
        </div>

        <div className="relative">
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center space-x-2 p-2 rounded-md hover:bg-[#312a56] "
          >
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
              <User className="h-5 w-5 text-white" />
            </div>
            <span className="hidden md:inline-block">{user ? `${user.first_name} ${user.last_name}` : "Carlos Rodríguez"}</span>
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
