import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import DownloadModal from '../DownloadModal';

// Mock window.innerWidth for responsive testing
const mockWindowSize = (width, height) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height,
  });
};

describe('DownloadModal Responsive Behavior', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    type: 'success',
    filename: 'test-file.pdf',
    message: 'Test message',
    autoCloseDelay: 0, // Disable auto-close for testing
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Mobile Responsive Features (< 640px)', () => {
    beforeEach(() => {
      mockWindowSize(375, 667); // iPhone SE size
    });

    test('should apply mobile-specific classes', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const modal = screen.getByRole('dialog');
      const modalContent = modal.querySelector('[class*="bg-[#1a1433]"]');
      
      // Check for mobile-specific classes
      expect(modalContent).toHaveClass('fixed', 'bottom-0', 'left-0', 'right-0');
      expect(modalContent).toHaveClass('rounded-b-none');
      expect(modalContent).toHaveClass('p-4'); // Mobile padding
    });

    test('should have proper touch targets (44px minimum)', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const closeButton = screen.getByLabelText('Cerrar modal');
      
      // Check minimum touch target size
      expect(closeButton).toHaveClass('min-w-[44px]', 'min-h-[44px]');
      expect(closeButton).toHaveClass('touch-manipulation');
    });

    test('should use mobile-optimized animations', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const modal = screen.getByRole('dialog');
      const modalContent = modal.querySelector('[class*="bg-[#1a1433]"]');
      
      // Check for mobile animation classes
      expect(modalContent).toHaveClass('slide-in-from-bottom-full');
      expect(modalContent).toHaveClass('transform-gpu');
      expect(modalContent).toHaveClass('backface-hidden');
    });
  });

  describe('Desktop Responsive Features (>= 640px)', () => {
    beforeEach(() => {
      mockWindowSize(1024, 768); // Desktop size
    });

    test('should apply desktop-specific classes', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const modal = screen.getByRole('dialog');
      const modalContent = modal.querySelector('[class*="bg-[#1a1433]"]');
      
      // Check for desktop-specific classes
      expect(modalContent).toHaveClass('sm:relative', 'sm:rounded-xl');
      expect(modalContent).toHaveClass('sm:bottom-auto', 'sm:left-auto', 'sm:right-auto');
      expect(modalContent).toHaveClass('md:p-6'); // Desktop padding
    });

    test('should use desktop-optimized animations', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const modal = screen.getByRole('dialog');
      const modalContent = modal.querySelector('[class*="bg-[#1a1433]"]');
      
      // Check for desktop animation classes
      expect(modalContent).toHaveClass('sm:zoom-in-95');
      expect(modalContent).toHaveClass('sm:slide-in-from-bottom-0');
    });
  });

  describe('Responsive Text and Spacing', () => {
    test('should have responsive text sizes', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const title = screen.getByText('Descarga Exitosa');
      const description = screen.getByText('Test message');
      
      // Check responsive text classes
      expect(title).toHaveClass('text-lg', 'sm:text-xl');
      expect(description).toHaveClass('text-sm', 'sm:text-base');
    });

    test('should have responsive spacing', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const modal = screen.getByRole('dialog');
      const headerDiv = modal.querySelector('.flex.items-start.justify-between');
      const contentDiv = modal.querySelector('.space-y-3');
      
      // Check responsive spacing classes
      expect(headerDiv).toHaveClass('mb-4', 'sm:mb-5');
      expect(contentDiv).toHaveClass('space-y-3', 'sm:space-y-4');
    });
  });

  describe('Accessibility Features', () => {
    test('should have proper ARIA attributes', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const modal = screen.getByRole('dialog');
      
      expect(modal).toHaveAttribute('aria-modal', 'true');
      expect(modal).toHaveAttribute('aria-labelledby', 'download-modal-title');
      expect(modal).toHaveAttribute('aria-describedby', 'download-modal-description');
    });

    test('should handle keyboard navigation', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const closeButton = screen.getByLabelText('Cerrar modal');
      
      // Test ESC key
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    test('should respect reduced motion preferences', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const modal = screen.getByRole('dialog');
      const modalContent = modal.querySelector('[class*="bg-[#1a1433]"]');
      
      // Check for reduced motion classes
      expect(modalContent).toHaveClass('motion-reduce:animate-none');
      expect(modalContent).toHaveClass('motion-reduce:transition-none');
    });
  });

  describe('Touch Interaction Handling', () => {
    test('should handle touch events for user interaction', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const modal = screen.getByRole('dialog');
      const modalContent = modal.querySelector('[class*="bg-[#1a1433]"]');
      
      // Simulate touch start
      fireEvent.touchStart(modalContent);
      
      // Should not throw errors and should handle the event
      expect(modalContent).toBeInTheDocument();
    });

    test('should handle backdrop touch for dismissal', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const backdrop = screen.getByRole('dialog');
      
      // Touch the backdrop (not the modal content)
      fireEvent.click(backdrop);
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  describe('Performance Optimizations', () => {
    test('should have performance optimization classes', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const modal = screen.getByRole('dialog');
      const modalContent = modal.querySelector('[class*="bg-[#1a1433]"]');
      
      // Check for performance classes
      expect(modalContent).toHaveClass('will-change-transform');
      expect(modalContent).toHaveClass('transform-gpu');
      expect(modalContent).toHaveClass('backface-hidden');
    });
  });

  describe('Error State Responsive Behavior', () => {
    test('should maintain responsive behavior in error state', () => {
      const errorProps = {
        ...defaultProps,
        type: 'error',
      };
      
      render(<DownloadModal {...errorProps} />);
      
      const title = screen.getByText('Error de Descarga');
      const icon = screen.getByRole('dialog').querySelector('[class*="text-red-400"]');
      
      // Check responsive classes are still applied
      expect(title).toHaveClass('text-lg', 'sm:text-xl');
      expect(icon.parentElement).toHaveClass('w-10', 'h-10', 'sm:w-12', 'sm:h-12');
    });
  });
});