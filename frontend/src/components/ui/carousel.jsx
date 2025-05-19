import { useRef, useEffect, useState } from "react";

export default function FaqCarousel({ items = [], speed = 30 }) {
  const [offset, setOffset] = useState(0);
  const [hovered, setHovered] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  const [noTransition, setNoTransition] = useState(false);
  const containerRef = useRef(null);


  const CARD_WIDTH = 250 + 32; 
  const totalCards = items.length;
  const cards = [...items, ...items]; 

  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      setOffset((prev) => prev + 1);
    }, 600 / speed);
    return () => clearInterval(interval);
  }, [isPaused, speed]);


  useEffect(() => {
    if (offset >= totalCards * CARD_WIDTH) {
      setNoTransition(true);
      setOffset(offset - totalCards * CARD_WIDTH);
    }
  }, [offset, totalCards, CARD_WIDTH]);

  useEffect(() => {
    if (noTransition) {
      const id = setTimeout(() => setNoTransition(false), 20);
      return () => clearTimeout(id);
    }
  }, [noTransition]);

  return (
    <div
      className="relative w-full max-w-7xl mx-auto py-8 select-none overflow-hidden"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div
        ref={containerRef}
        className="flex gap-8"
        style={{
          transform: `translateX(-${offset}px)`,
          transition: noTransition
            ? "none"
            : isPaused
            ? "none"
            : "transform 0.03s linear",
        }}
      >
        {cards.map((item, idx) => (
          <div
            key={idx}
            className={`flex-shrink-0 w-80 transition-transform duration-300 ${
              hovered === idx ? "scale-105 z-10" : "scale-100"
            }`}
            onMouseEnter={() => setHovered(idx)}
            onMouseLeave={() => setHovered(null)}
            style={{ pointerEvents: "auto" }}
          >
            <div className="bg-dark rounded-2xl shadow-lg p-8 h-40 flex flex-col items-center border border-[#312a56]">
              <h5 className="text-lg font-bold text-primary text-center mb-4">{item.title}</h5>
              <p className="text-gray-200 text-center text-base">{item.content}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}