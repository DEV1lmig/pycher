'use client'
import dynamic from "next/dynamic";
const HeroAnimated = dynamic(() => import('./HeroAnimation').then(mod => mod.default), {
    ssr: false
})

export default function Hero() {

  return (
    <HeroAnimated />
  );
}
