import React, { useEffect, useRef } from 'react';
import { X, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const DownloadModal = ({
  isOpen,
  onClose,
  type,
  filename,
  message,
  autoCloseDelay = 3000
}) => {
  const modalRef = useRef(null);
  const closeButtonRef = useRef(null);
  const autoCloseTimerRef = useRef(null);
  const countdownIntervalRef = useRef(null);
  const previousActiveElementRef = useRef(null);
  const [remainingTime, setRemainingTime] = React.useState(autoCloseDelay);
  const [isTimerActive, setIsTimerActive] = React.useState(false);
  const [announceText, setAnnounceText] = React.useState('');

  // Auto-dismiss functionality with countdown
  useEffect(() => {
    if (isOpen && autoCloseDelay > 0) {
      setRemainingTime(autoCloseDelay);
      setIsTimerActive(true);

      // Set up the main auto-close timer
      autoCloseTimerRef.current = setTimeout(() => {
        onClose();
      }, autoCloseDelay);

      // Set up countdown interval for display
      countdownIntervalRef.current = setInterval(() => {
        setRemainingTime((prev) => {
          const newTime = prev - 100;
          return newTime <= 0 ? 0 : newTime;
        });
      }, 100);
    }

    return () => {
      if (autoCloseTimerRef.current) {
        clearTimeout(autoCloseTimerRef.current);
      }
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }
      setIsTimerActive(false);
    };
  }, [isOpen, autoCloseDelay, onClose]);

  // Focus management and keyboard navigation
  useEffect(() => {
    if (isOpen) {
      // Store the previously focused element to restore focus later
      previousActiveElementRef.current = document.activeElement;

      // Focus the close button when modal opens
      if (closeButtonRef.current) {
        closeButtonRef.current.focus();
      }

      // Set up screen reader announcement
      const isSuccess = type === 'success';
      const announcement = isSuccess 
        ? `Descarga exitosa. ${filename ? `Archivo ${filename} descargado.` : 'Archivo descargado correctamente.'} ${message || ''}`
        : `Error de descarga. ${message || 'Hubo un problema al descargar el archivo.'} ${filename ? `Archivo: ${filename}` : ''}`;
      
      setAnnounceText(announcement);

      // Prevent body scrolling and improve mobile experience
      document.body.style.overflow = 'hidden';
      // Prevent iOS Safari bounce scrolling
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';

      // Handle ESC key
      const handleEscKey = (event) => {
        if (event.key === 'Escape') {
          onClose();
        }
      };

      // Enhanced focus trap with better accessibility
      const handleTabKey = (event) => {
        if (event.key === 'Tab') {
          const focusableElements = modalRef.current?.querySelectorAll(
            'button:not([disabled]), [href]:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])'
          );
          
          if (focusableElements && focusableElements.length > 0) {
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (event.shiftKey) {
              if (document.activeElement === firstElement) {
                event.preventDefault();
                lastElement.focus();
              }
            } else {
              if (document.activeElement === lastElement) {
                event.preventDefault();
                firstElement.focus();
              }
            }
          }
        }
      };

      document.addEventListener('keydown', handleEscKey);
      document.addEventListener('keydown', handleTabKey);

      return () => {
        document.removeEventListener('keydown', handleEscKey);
        document.removeEventListener('keydown', handleTabKey);
        // Restore body scroll behavior
        document.body.style.overflow = 'unset';
        document.body.style.position = 'unset';
        document.body.style.width = 'unset';
        
        // Restore focus to the previously focused element
        if (previousActiveElementRef.current && typeof previousActiveElementRef.current.focus === 'function') {
          try {
            previousActiveElementRef.current.focus();
          } catch (error) {
            // Fallback if the element is no longer focusable
            console.warn('Could not restore focus to previous element:', error);
          }
        }
      };
    }
  }, [isOpen, onClose, type, filename, message]);

  // Handle backdrop click
  const handleBackdropClick = (event) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  // Clear auto-close timer on user interaction
  const handleUserInteraction = () => {
    if (autoCloseTimerRef.current) {
      clearTimeout(autoCloseTimerRef.current);
      autoCloseTimerRef.current = null;
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = null;
    }
    setIsTimerActive(false);
  };

  if (!isOpen) return null;

  const isSuccess = type === 'success';
  const isError = type === 'error';

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-3 sm:p-4 md:p-6"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="download-modal-title"
      aria-describedby="download-modal-description"
      aria-live="polite"
    >
      <div
        ref={modalRef}
        className={cn(
          // Base styles
          "bg-[#1a1433] border border-[#312a56] rounded-xl shadow-2xl",
          // Responsive sizing and spacing
          "w-full max-w-[90vw] mx-auto",
          "p-4 sm:p-5 md:p-6",
          // Mobile-first responsive width constraints
          "sm:max-w-md md:max-w-lg lg:max-w-xl",
          // Mobile positioning - bottom sheet style on small screens
          "fixed bottom-0 left-0 right-0 rounded-b-none sm:relative sm:rounded-xl",
          "sm:bottom-auto sm:left-auto sm:right-auto",
          // Animations with mobile optimization
          "transform transition-all duration-200 ease-out",
          "animate-in fade-in-0 slide-in-from-bottom-full sm:slide-in-from-bottom-4 sm:zoom-in-95",
          "sm:slide-in-from-bottom-0", // No slide on larger screens
          // Performance and accessibility
          "motion-reduce:animate-none motion-reduce:transition-none", // Respect reduced motion preferences
          "will-change-transform", // Optimize for animations
          // Mobile performance optimizations
          "transform-gpu", // Use GPU acceleration
          "backface-hidden" // Prevent flickering on mobile
        )}
        onClick={handleUserInteraction}
        onMouseEnter={handleUserInteraction}
        onFocus={handleUserInteraction}
        onTouchStart={handleUserInteraction}
      >
        {/* Header with icon and close button */}
        <div className="flex items-start justify-between mb-4 sm:mb-5">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            {isSuccess && (
              <div className="flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 bg-green-500/20 rounded-full flex items-center justify-center">
                <CheckCircle className="w-6 h-6 sm:w-7 sm:h-7 text-green-400" />
              </div>
            )}
            {isError && (
              <div className="flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 bg-red-500/20 rounded-full flex items-center justify-center">
                <AlertCircle className="w-6 h-6 sm:w-7 sm:h-7 text-red-400" />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <h3
                id="download-modal-title"
                className={cn(
                  "text-lg sm:text-xl font-semibold truncate",
                  isSuccess && "text-green-400",
                  isError && "text-red-400"
                )}
              >
                {isSuccess ? 'Descarga Exitosa' : 'Error de Descarga'}
              </h3>
            </div>
          </div>
          
          <Button
            ref={closeButtonRef}
            variant="ghost"
            size="icon"
            onClick={onClose}
            className={cn(
              "text-gray-400 hover:text-white hover:bg-[#312a56] flex-shrink-0 ml-2",
              // Ensure minimum touch target size (44px)
              "min-w-[44px] min-h-[44px] w-11 h-11 sm:w-10 sm:h-10",
              "touch-manipulation", // Optimize for touch
              "-mt-1 -mr-1 sm:mt-0 sm:mr-0"
            )}
            aria-label="Cerrar modal"
          >
            <X className="w-5 h-5 sm:w-4 sm:h-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="space-y-3 sm:space-y-4">
          <div
            id="download-modal-description"
            className="text-gray-300 text-sm sm:text-base leading-relaxed"
          >
            {message || (isSuccess 
              ? 'Tu archivo se ha descargado correctamente.' 
              : 'Hubo un problema al descargar el archivo.'
            )}
          </div>
          
          {filename && (
            <div className="bg-[#160f30] border border-[#312a56] rounded-lg p-3 sm:p-4">
              <div className="text-xs sm:text-sm text-gray-400 mb-1 sm:mb-2">Archivo:</div>
              <div className="text-white font-medium text-sm sm:text-base break-all leading-relaxed">
                {filename}
              </div>
            </div>
          )}
        </div>

        {/* Auto-close indicator */}
        {autoCloseDelay > 0 && isTimerActive && (
          <div className="mt-4 sm:mt-5 text-xs sm:text-sm text-gray-500 text-center leading-relaxed">
            Este modal se cerrará automáticamente en {Math.ceil(remainingTime / 1000)} segundos
          </div>
        )}

        {/* Screen reader announcement - visually hidden but accessible */}
        <div
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
          role="status"
        >
          {announceText}
        </div>
      </div>
    </div>
  );
};

export default DownloadModal;