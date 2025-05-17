"use client"

import { useState } from "react"
import { Link, useNavigate } from "@tanstack/react-router"
import { Home, BookOpen, Code, Settings, HelpCircle, LogOut } from "lucide-react"
import { cn } from "@/lib/utils"
import { logout } from "@/lib/auth";

import { VscHome, VscArchive, VscAccount, VscSettingsGear } from "react-icons/vsc";
  

export function DashboardSidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate();

  const toggleSidebar = () => {
    setCollapsed(!collapsed)
  }

  const handleLogout = () => {
    logout();
    navigate({ to: "/login" });
  };

  const menuItems = [
    { icon: Home, label: "Inicio", href: "/home" },
    { icon: BookOpen, label: "Mis Cursos", href: "/home/courses" },
    { icon: Code, label: "Ejercicios", href: "/home/exercises" },
  ]

  const bottomMenuItems = [
    { icon: HelpCircle, label: "FAQ", href: "/home/help" },
    { icon: LogOut, label: "Cerrar Sesión", onClick: handleLogout },
  ]

  return (
    <aside
      className={cn("bg-[#1a1433] h-screen transition-all duration-300 flex flex-col", collapsed ? "w-16" : "w-64")}
    >
      <div className="p-4 flex items-center justify-between border-b border-[#312a56] h-[81px]">
        <div className={cn("flex items-center", collapsed && "justify-center w-full ")}>
          {!collapsed && (
            <span className="text-xl font-bold text-white ml-2">
              <span className="text-[#f2d231]">Py</span>Cher
            </span>
          )}
          {collapsed && <span className="text-xl font-bold text-[#f2d231]">P</span>}
        </div>
        <button onClick={toggleSidebar} className="text-gray-400 hover:text-white">
          {collapsed ? "→" : "←"}
        </button>
      </div>

      

      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-2 px-2">
          {menuItems.map((item, index) => (
            <li key={index}>
              <Link
                href={item.href}
                className={cn(
                  "flex items-center p-2 rounded-md hover:bg-[#312a56] transition-colors",
                  item.href === "/dashboard" && "bg-[#312a56]",
                )}
              >
                <item.icon className="h-5 w-5 text-[#9980f2]" />
                {!collapsed && <span className="ml-3">{item.label}</span>}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-[#312a56]">
        <ul className="space-y-2">
          {bottomMenuItems.map((item, index) => (
            <li key={index}>
              <button
                className="flex items-center p-2 rounded-md hover:bg-[#312a56] transition-colors w-full text-left"
                onClick={item.onClick ? item.onClick : () => navigate({ to: item.href })}
              >
                <item.icon className="h-5 w-5 text-[#9980f2]" />
                {!collapsed && <span className="ml-3">{item.label}</span>}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  )
}
