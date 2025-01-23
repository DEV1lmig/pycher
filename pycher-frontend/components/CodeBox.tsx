'use client'

import { useEffect, useRef } from 'react';
import { Bot } from 'lucide-react';
import { gsap } from 'gsap';

export default function CodeBox() {
  const editorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power2.out' } });

    tl.fromTo(editorRef.current,
      { x: 100, opacity: 0 },
      { x: 0, opacity: 1, duration: 1, delay: 0.5 }
    );

    const elements = editorRef.current?.querySelectorAll('.animate-item');
    elements?.forEach((el, index) => {
      tl.fromTo(el,
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4 },
        `-=${index ? 0.2 : 0}`
      );
    });

    return () => {
      tl.kill();
    };
  }, []);

  return (
    <div ref={editorRef} className="relative">
      <div className="bg-base/10 backdrop-blur-sm p-6 rounded-xl shadow-2xl">
        <div className="animate-item flex items-center gap-3 mb-4">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
        </div>

        <pre className="animate-item text-sm font-mono">
          <code className="text-primary">def</code>
          <code className="text-base"> calculate_average(numbers):</code>
          <br />
          <code className="text-base">    return sum(numbers) / len(numbers)</code>
        </pre>

        <div className="animate-item mt-4 p-4 bg-primary/10 rounded-lg border border-primary/30">
          <div className="flex items-start gap-3">
            <Bot className="w-6 h-6 text-primary mt-1" />
            <div>
              <p className="text-sm text-primary">AI Assistant</p>
              <p className="text-base">Great work! Consider adding error handling for empty lists to make your function more robust.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
