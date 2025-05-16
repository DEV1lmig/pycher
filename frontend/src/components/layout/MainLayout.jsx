// filepath: /home/dev1mig/Documents/projects/pycher/frontend/src/components/layout/MainLayout.jsx
import { useState } from 'react';
import { Link } from '@tanstack/react-router';
import { MoonIcon, SunIcon, CodeIcon, MenuIcon } from 'lucide-react';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';

export function MainLayout({ children }) {
  const [theme, setTheme] = useState('light');

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 w-full border-b bg-background">
        <div className="container flex h-16 items-center px-4">
          <Link to="/" className="flex items-center gap-2 font-bold">
            <CodeIcon className="h-6 w-6" />
            <span>Python Learning Platform</span>
          </Link>
          <nav className="ml-auto flex gap-4">
            <Link to="/" className="hover:text-primary">Dashboard</Link>
            <Link to="/module/beginner" className="hover:text-primary">Beginner</Link>
            <Link to="/module/intermediate" className="hover:text-primary">Intermediate</Link>
            <Link to="/module/advanced" className="hover:text-primary">Advanced</Link>
          </nav>
          <Button variant="ghost" size="icon" onClick={toggleTheme} className="ml-4">
            {theme === 'light' ? <MoonIcon className="h-5 w-5" /> : <SunIcon className="h-5 w-5" />}
          </Button>
        </div>
      </header>
      <main className="container py-6">{children}</main>
    </div>
  );
}
