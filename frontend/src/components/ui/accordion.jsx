import { useState } from "react";
import { ArrowDown } from "lucide-react";

export default function Accordion({ items = [] }) {
  const [expanded, setExpanded] = useState(null);

  const handleToggle = (idx) => {
    setExpanded(expanded === idx ? null : idx);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {items.map((item, idx) => (
        <div key={idx} className="mb-2 border border-primary-light rounded-lg bg-dark">
          <button
            className="w-full flex justify-between items-center p-4 focus:outline-none"
            onClick={() => handleToggle(idx)}
            aria-expanded={expanded === idx}
            aria-controls={`panel${idx}-content`}
            id={`panel${idx}-header`}
          >
            <div className="flex flex-col text-left">
              <span className="font-semibold text-white">{item.title}</span>
              {item.subtitle && (
                <span className="text-sm text-gray-400">{item.subtitle}</span>
              )}
            </div>
            <span
              className={`transform transition-transform duration-200 text-gray-400 ${
                expanded === idx ? "rotate-180" : ""
              }`}
            >
              <ArrowDown className="h-4 w-4 ml-1" />
            </span>
          </button>
          <div
            id={`panel${idx}-content`}
            className={`overflow-hidden transition-all duration-300 ${
              expanded === idx ? "max-h-40 p-4" : "max-h-0 p-0"
            }`}
            aria-labelledby={`panel${idx}-header`}
          >
            <div className="text-gray-300">{item.content}</div>
          </div>
        </div>
      ))}
    </div>
  );
}