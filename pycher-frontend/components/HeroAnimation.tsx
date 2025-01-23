'use client'

import { useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { gsap } from 'gsap';
import CodeBox from '@/components/CodeBox'


export default function HeroAnimated() {
  const heroRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const buttonsContainerRef = useRef<HTMLDivElement>(null);
  const startButtonRef = useRef<HTMLButtonElement>(null);
  const curriculumButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    tl.fromTo(titleRef.current,
      { y: 100, opacity: 0 },
      { y: 0, opacity: 1, duration: 1 }
    )
    .fromTo(subtitleRef.current,
      { y: 50, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.8 }
    )
    .fromTo(buttonsContainerRef.current,
      { y: 30, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6 },
      '-=0.3'
    );

    return () => {
      tl.kill();
    };
  }, []);

  return (
    <div className="min-h-screen flex items-center bg-background text-base" ref={heroRef}>
        <div className="max-w-7xl mx-auto px-6 py-32 grid lg:grid-cols-2 gap-12 items-center w-full">
          <div className="space-y-8">
            <h1 ref={titleRef} className="text-4xl md:text-6xl font-bold leading-tight">
              Master Python with
              <span className="text-primary"> AI-Powered</span> Learning
            </h1>
            <p ref={subtitleRef} className="text-xl opacity-90">Master Python with interactive courses and real-time AI assistance.
            Get instant feedback and personalized guidance.</p>
            <div className="flex flex-col sm:flex-row gap-4" ref={buttonsContainerRef}>
              <Button ref={startButtonRef} size="lg" className="gap-2">
                <Sparkles className="w-5 h-5" />
                Start Learning Free
              </Button>
              <Button ref={curriculumButtonRef} size="lg" variant="secondary">
                View Curriculum
              </Button>
            </div>
            </div>
            <CodeBox />
          </div>
        </div>
  );
}
