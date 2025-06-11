import * as React from "react"

import { cn } from "@/lib/utils"

const Textarea = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        // Base styles
        "flex min-h-[60px] w-full rounded-lg border border-primary-opaque/30 bg-primary-opaque/70 px-4 py-3 text-base text-gray-100 shadow-sm",
        // Focus and placeholder
        "placeholder:text-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary focus-visible:border-secondary",
        // Disabled
        "disabled:cursor-not-allowed disabled:opacity-50",
        // Responsive
        "md:text-sm",
        className
      )}
      ref={ref}
      {...props}
    />
  );
})
Textarea.displayName = "Textarea"

export { Textarea }
