"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Image from 'next/image'
import laptopPic from '@/assets/images/laptop.png'

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      router.push("/dashboard");
    }, 1000);
  };

  return (
    <div className="flex min-h-screen">
      <div className="hidden lg:flex lg:w-[60%] relative p-12 flex-col justify-between">
        <div className="font-gelasio text-3xl font-bold text-white">
          <span className="text-secondary">Py</span>
          <span>Cher</span>
        </div>
        <div className="space-y-6">
          <h1 className="text-4xl font-bold text-white font-gelasio flex flex-col items-end -mt-60 text-right">
            Start learning the best<br />
            tool for data analizys<br />
            with us at<br />
            PyCher<br />
            Sign up now!
          </h1>
          <div className="absolute bottom-0 left-0">
            <Image
                src={laptopPic}
                alt="Laptop"
                className="mix-blend-luminosity filter brightness-75 opacity-80"
                // width={500} automatically provided
                // height={500} automatically provided
                // blurDataURL="data:..." automatically provided
                // placeholder="blur" // Optional blur-up while loading
                />
          </div>
        </div>
        <div className="font-gelasio text-3xl font-bold text-white/20 justify-end w-full flex">
          PyC
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center p-8 bg-white rounded-l-[40px]">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold">WELCOME</h2>
            <p className="text-muted-foreground mt-2">
              Sign up to start with your adventure in python
            </p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                placeholder="Placeholder"
                className="h-12"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Placeholder"
                className="h-12"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Placeholder"
                className="h-12"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Placeholder"
                className="h-12"
                required
              />
            </div>
            <Button
              className="w-full h-12 text-lg bg-primary hover:bg-[#00a884]"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? "Signing up..." : "Sign Up"}
            </Button>
            <Button
              variant="outline"
              className="w-full h-12 text-lg bg-transparent"
              type="button"
            >
              <img
                src="https://www.google.com/favicon.ico"
                alt="Google"
                className="w-5 h-5 mr-2"
              />
              Sign up with Google
            </Button>
          </form>
          <p className="text-center text-muted-foreground">
            Already have an account?{" "}
            <Link href="/auth/login" className="text-[#00b894] hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
