'use client'

import { useEffect, useRef } from 'react';
import { Check } from 'lucide-react';
import { Button } from './ui/button';
import { fadeInUp } from '@/libs/animations';

export default function Pricing() {
  const pricingRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (pricingRef.current) {
      fadeInUp(pricingRef.current);
    }
  }, []);

  const plans = [
    {
      name: "Basic",
      price: "Free",
      features: [
        "Access to basic Python courses",
        "Limited AI assistance",
        "Community support",
        "Basic code editor"
      ]
    },
    {
      name: "Pro",
      price: "$19/month",
      features: [
        "All basic features",
        "Unlimited AI assistance",
        "Advanced courses",
        "Priority support",
        "Advanced code editor"
      ],
      popular: true
    }
  ];

  return (
    <section id="pricing" className="py-20 bg-secondary/30">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-background">Simple, Transparent Pricing</h2>
          <p className="mt-4 text-xl text-background/80">Start learning Python with AI assistance today</p>
        </div>

        <div ref={pricingRef} className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative p-8 rounded-xl bg-base ${plan.popular ? 'border-2 border-primary' : 'border border-secondary'}`}
            >
              {plan.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-white text-sm rounded-full">
                  Most Popular
                </span>
              )}
              <h3 className="text-2xl font-bold text-background">{plan.name}</h3>
              <p className="mt-4 text-4xl font-bold text-background">{plan.price}</p>
              <ul className="mt-8 space-y-4">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-primary" />
                    <span className="text-background/70">{feature}</span>
                  </li>
                ))}
              </ul>
              <Button
                variant={plan.popular ? "default" : "secondary"}
                className="mt-8 w-full"
              >
                Get Started
              </Button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
