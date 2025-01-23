import { Code2, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="fixed top-0 w-full bg-background/95 backdrop-blur-sm z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Code2 className="w-8 h-8 text-primary" />
          <span className="text-xl font-bold text-base"><span className='text-secondary'>Py</span>Cher</span>
        </div>

        <div className="hidden md:flex items-center space-x-8 text-base/80">
          <a href="#features" className="hover:text-primary transition-colors">Features</a>
          <a href="#how-it-works" className="hover:text-primary transition-colors">How it Works</a>
          <a href="#pricing" className="hover:text-primary transition-colors">Pricing</a>
        </div>

        <div className="flex items-center space-x-4">
        <Link href="/auth/login">
    <Button variant="ghost" className="hidden text-base md:block">
      Sign In
    </Button>
  </Link>
  <Link href="/auth/register">
    <Button>
      Get Started
    </Button>
  </Link>
          <Menu className="md:hidden w-6 h-6 text-base" />
        </div>
      </div>
    </nav>
  );
}
