import { useEffect, useState } from "react";
import logo from "@/assets/img/logo.png";
import AnimatedContent from "@/components/ui/animated-content";
import TiltedCard from "@/components/ui/tilted-card.jsx";

export default function AuthLayout({ children, isRegister }) {
  const [animateToRegister, setAnimateToRegister] = useState(isRegister);

  return (
    <main className="relative flex min-h-screen overflow-hidden bg-dark">
      <div
        className={`relative z-10 hidden md:flex md:w-1/2 bg-gradient-to-br from-[#160f30] via-[#312a56] to-[#312a56] items-center justify-center p-10 transition-transform duration-700 ${
          animateToRegister ? "translate-x-full" : "translate-x-0"
        }`}
      >
        <AnimatedContent
          distance={150}
          direction="vertical"
          reverse={true}
          config={{ tension: 60, friction: 20 }}
          initialOpacity={0.2}
          animateOpacity
          scale={1.1}
          threshold={0.2}
        >
          <div className="text-center">
            <div className="text-white text-4xl font-bold mb-8 flex items-center justify-center">
              <TiltedCard
                imageSrc={logo}
                altText="logo"
                containerHeight="320px"
                containerWidth="320px"
                imageHeight="270px"
                imageWidth="270px"
                rotateAmplitude={12}
                scaleOnHover={1.2}
                showMobileWarning={false}
                showTooltip={false}
                displayOverlayContent={false}
              />
            </div>
          </div>
        </AnimatedContent>
      </div>

      <div
        className={`w-full md:w-1/2 bg-[#160f30] flex items-center justify-center p-4 transition-transform duration-700 ${
          isRegister ? "-translate-x-full" : "translate-x-0"
        }`}
      >
        <AnimatedContent
          distance={150}
          direction="vertical"
          reverse={false}
          config={{ tension: 60, friction: 20 }}
          initialOpacity={0.2}
          animateOpacity
          scale={1.1}
          threshold={0.2}
        >
          <div className="w-full max-w-md space-y-6">{children}</div>
        </AnimatedContent>
      </div>
    </main>
  );
}
