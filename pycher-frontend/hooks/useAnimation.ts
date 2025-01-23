import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

type AnimationFunction = (element: Element) => gsap.core.Tween;

export const useAnimation = (animation: AnimationFunction) => {
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!elementRef.current) return;

    const element = elementRef.current;
    let tween = animation(element);

    return () => {
      tween.kill();
    };
  }, [animation]);

  return elementRef;
};

export const useScrollAnimation = (animation: AnimationFunction) => {
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!elementRef.current) return;

    const element = elementRef.current;

    const tween = animation(element);

    ScrollTrigger.create({
      trigger: element,
      start: 'top 80%',
      animation: tween
    });

    return () => {
      tween.kill();
    };
  }, [animation]);

  return elementRef;
};
