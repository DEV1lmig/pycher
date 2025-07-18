import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import DownloadModal from '../DownloadModal';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

describe('DownloadModal Accessibility', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    type: 'success',
    filename: 'test-file.pdf',
    message: 'Test message'
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset document body styles
    document.body.style.overflow = 'unset';
    document.body.style.position = 'unset';
    document.body.style.width = 'unset';
  });

  afterEach(() => {
    // Clean up any remaining timers
    jest.clearAllTimers();
  });

  describe('ARIA Labels and Roles', () => {
    it('should have proper dialog role and aria attributes', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'download-modal-title');
      expect(dialog).toHaveAttribute('aria-describedby', 'download-modal-description');
      expect(dialog).toHaveAttribute('aria-live', 'polite');
    });

    it('should have proper heading with correct id', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const heading = screen.getByRole('heading', { level: 3 });
      expect(heading).toHaveAttribute('id', 'download-modal-title');
      expect(heading).toHaveTextContent('Descarga Exitosa');
    });

    it('should have proper description with correct id', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const description = document.getElementById('download-modal-description');
      expect(description).toBeInTheDocument();
      expect(description).toHaveTextContent('Test message');
    });

    it('should have close button with proper aria-label', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const closeButton = screen.getByRole('button', { name: /cerrar modal/i });
      expect(closeButton).toBeInTheDocument();
      expect(closeButton).toHaveAttribute('aria-label', 'Cerrar modal');
    });

    it('should have screen reader announcement with proper attributes', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveAttribute('aria-live', 'polite');
      expect(announcement).toHaveAttribute('aria-atomic', 'true');
      expect(announcement).toHaveClass('sr-only');
    });
  });

  describe('Focus Management', () => {
    it('should focus close button when modal opens', async () => {
      render(<DownloadModal {...defaultProps} />);
      
      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /cerrar modal/i });
        expect(closeButton).toHaveFocus();
      });
    });

    it('should restore focus to previous element when modal closes', async () => {
      // Create a button to focus before opening modal
      const TestComponent = () => {
        const [isOpen, setIsOpen] = React.useState(false);
        return (
          <div>
            <button onClick={() => setIsOpen(true)}>Open Modal</button>
            <DownloadModal
              {...defaultProps}
              isOpen={isOpen}
              onClose={() => setIsOpen(false)}
            />
          </div>
        );
      };

      render(<TestComponent />);
      
      const openButton = screen.getByText('Open Modal');
      await userEvent.click(openButton);
      
      // Modal should be open and close button focused
      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /cerrar modal/i });
        expect(closeButton).toHaveFocus();
      });
      
      // Close modal
      const closeButton = screen.getByRole('button', { name: /cerrar modal/i });
      await userEvent.click(closeButton);
      
      // Focus should return to open button
      await waitFor(() => {
        expect(openButton).toHaveFocus();
      });
    });

    it('should trap focus within modal', async () => {
      render(<DownloadModal {...defaultProps} />);
      
      const closeButton = screen.getByRole('button', { name: /cerrar modal/i });
      
      // Tab should stay within modal (only one focusable element in this case)
      await userEvent.tab();
      expect(closeButton).toHaveFocus();
      
      // Shift+Tab should also stay within modal
      await userEvent.tab({ shift: true });
      expect(closeButton).toHaveFocus();
    });
  });

  describe('Keyboard Navigation', () => {
    it('should close modal when Escape key is pressed', async () => {
      const onClose = jest.fn();
      render(<DownloadModal {...defaultProps} onClose={onClose} />);
      
      fireEvent.keyDown(document, { key: 'Escape' });
      
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should handle Tab key for focus trapping', async () => {
      render(<DownloadModal {...defaultProps} />);
      
      const closeButton = screen.getByRole('button', { name: /cerrar modal/i });
      
      // Simulate Tab key press
      fireEvent.keyDown(document, { key: 'Tab' });
      
      // Focus should remain on close button (only focusable element)
      expect(closeButton).toHaveFocus();
    });

    it('should handle Shift+Tab key for reverse focus trapping', async () => {
      render(<DownloadModal {...defaultProps} />);
      
      const closeButton = screen.getByRole('button', { name: /cerrar modal/i });
      
      // Simulate Shift+Tab key press
      fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
      
      // Focus should remain on close button (only focusable element)
      expect(closeButton).toHaveFocus();
    });
  });

  describe('Screen Reader Announcements', () => {
    it('should announce success state correctly', () => {
      render(<DownloadModal {...defaultProps} type="success" />);
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent(/descarga exitosa.*test-file\.pdf.*descargado.*test message/i);
    });

    it('should announce error state correctly', () => {
      render(<DownloadModal {...defaultProps} type="error" />);
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent(/error de descarga.*test message.*test-file\.pdf/i);
    });

    it('should handle missing filename gracefully', () => {
      render(<DownloadModal {...defaultProps} filename="" />);
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent(/archivo descargado correctamente/i);
    });

    it('should handle missing message gracefully', () => {
      render(<DownloadModal {...defaultProps} message="" />);
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent(/descarga exitosa.*test-file\.pdf.*descargado/i);
    });
  });

  describe('Reduced Motion Support', () => {
    it('should respect reduced motion preferences', () => {
      // Mock prefers-reduced-motion
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      render(<DownloadModal {...defaultProps} />);
      
      const modalContent = screen.getByRole('dialog').firstChild;
      expect(modalContent).toHaveClass('motion-reduce:animate-none');
      expect(modalContent).toHaveClass('motion-reduce:transition-none');
    });
  });

  describe('Body Scroll Prevention', () => {
    it('should prevent body scrolling when modal is open', () => {
      render(<DownloadModal {...defaultProps} />);
      
      expect(document.body.style.overflow).toBe('hidden');
      expect(document.body.style.position).toBe('fixed');
      expect(document.body.style.width).toBe('100%');
    });

    it('should restore body scrolling when modal is closed', () => {
      const { rerender } = render(<DownloadModal {...defaultProps} />);
      
      // Modal is open, body scroll should be prevented
      expect(document.body.style.overflow).toBe('hidden');
      
      // Close modal
      rerender(<DownloadModal {...defaultProps} isOpen={false} />);
      
      // Body scroll should be restored
      expect(document.body.style.overflow).toBe('unset');
      expect(document.body.style.position).toBe('unset');
      expect(document.body.style.width).toBe('unset');
    });
  });

  describe('Touch Targets', () => {
    it('should have minimum touch target size for close button', () => {
      render(<DownloadModal {...defaultProps} />);
      
      const closeButton = screen.getByRole('button', { name: /cerrar modal/i });
      expect(closeButton).toHaveClass('min-w-[44px]');
      expect(closeButton).toHaveClass('min-h-[44px]');
      expect(closeButton).toHaveClass('touch-manipulation');
    });
  });

  describe('Accessibility Compliance', () => {
    it('should not have any accessibility violations', async () => {
      const { container } = render(<DownloadModal {...defaultProps} />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in error state', async () => {
      const { container } = render(<DownloadModal {...defaultProps} type="error" />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Backdrop Click', () => {
    it('should close modal when backdrop is clicked', async () => {
      const onClose = jest.fn();
      render(<DownloadModal {...defaultProps} onClose={onClose} />);
      
      const backdrop = screen.getByRole('dialog');
      await userEvent.click(backdrop);
      
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should not close modal when modal content is clicked', async () => {
      const onClose = jest.fn();
      render(<DownloadModal {...defaultProps} onClose={onClose} />);
      
      const modalContent = screen.getByRole('dialog').firstChild;
      await userEvent.click(modalContent);
      
      expect(onClose).not.toHaveBeenCalled();
    });
  });
});