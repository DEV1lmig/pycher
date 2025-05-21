import { Link } from "@tanstack/react-router";

export default function Breadcrumbs({ items }) {
  return (
    <nav className="flex items-center text-sm mb-6 cursor-pointer" aria-label="Breadcrumb">
      {items.map((item, idx) => (
        <div key={idx} className="flex items-center">
          {idx > 0 && <span className="mx-2 text-gray-400">/</span>}
          {item.href ? (
            <Link
              to={item.href}
              className="flex items-center text-gray-400 hover:text-primary transition-colors duration-400 ease-in-out transition-all"
            >
              {item.icon && <span className="mr-1">{item.icon}</span>}
              {item.label}
            </Link>
          ) : (
            <span className="flex items-center text-primary font-semibold">
              {item.icon && <span className="mr-1">{item.icon}</span>}
              {item.label}
            </span>
          )}
        </div>
      ))}
    </nav>
  );
}