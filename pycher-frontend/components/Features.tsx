'use client'

import  { useEffect, useRef } from 'react';
import { Bot, Brain, Code2, Zap } from 'lucide-react';
import { staggerChildren } from '@/libs/animations';

export default function Features() {
  const featuresRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (featuresRef.current) {
      staggerChildren(featuresRef.current, '.feature-card');
    }
  }, []);

  const features = [
    {
      icon: <Bot className="w-8 h-8 text-primary" />,
      title: "AI-Powered Assistant",
      description: "Get instant help with errors and personalized explanations for complex concepts."
    },
    {
      icon: <Code2 className="w-8 h-8 text-primary" />,
      title: "Interactive Coding",
      description: "Practice Python in real-time with our built-in code editor and immediate feedback."
    },
    {
      icon: <Brain className="w-8 h-8 text-primary" />,
      title: "Adaptive Learning",
      description: "Courses adapt to your learning pace and style for optimal understanding."
    },
    {
      icon: <Zap className="w-8 h-8 text-primary" />,
      title: "Instant Feedback",
      description: "Receive immediate feedback on your code and suggestions for improvement."
    }
  ];

  return (
    <section id="features" className="py-20 bg-base">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-background">Why Choose PyCher?</h2>
          <p className="mt-4 text-xl text-background/80">Everything you need to master Python programming</p>
        </div>

        <div ref={featuresRef} className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="feature-card p-6 rounded-xl bg-white shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-background mb-2">{feature.title}</h3>
              <p className="text-background/70">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
