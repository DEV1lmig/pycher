import { useContext, useCallback } from 'react';
import DownloadNotificationContext from '../context/DownloadNotificationContext';

/**
 * Custom hook for managing download notifications
 * Provides convenient methods for showing success and error notifications
 * 
 * @returns {Object} Object containing notification methods
 * @throws {Error} If used outside of DownloadNotificationProvider
 */
export function useDownloadNotification() {
  const context = useContext(DownloadNotificationContext);
  
  // Error handling for context usage
  if (!context) {
    throw new Error(
      'useDownloadNotification must be used within a DownloadNotificationProvider. ' +
      'Make sure your component is wrapped with DownloadNotificationProvider.'
    );
  }

  const { showDownloadNotification, hideDownloadNotification } = context;

  /**
   * Show a success notification for a successful download
   * @param {string} filename - The name of the downloaded file
   * @param {string} [message] - Optional custom success message
   * @param {number} [autoCloseDelay=3000] - Auto-close delay in milliseconds
   */
  const showSuccess = useCallback((filename, message = '', autoCloseDelay = 3000) => {
    if (!filename || typeof filename !== 'string') {
      throw new Error('filename is required and must be a string');
    }

    showDownloadNotification({
      type: 'success',
      filename,
      message: message || `${filename} se ha descargado exitosamente`,
      autoCloseDelay
    });
  }, [showDownloadNotification]);

  /**
   * Show an error notification for a failed download
   * @param {string} filename - The name of the file that failed to download
   * @param {string} [message] - Optional custom error message
   * @param {number} [autoCloseDelay=5000] - Auto-close delay in milliseconds (longer for errors)
   */
  const showError = useCallback((filename, message = '', autoCloseDelay = 5000) => {
    if (!filename || typeof filename !== 'string') {
      throw new Error('filename is required and must be a string');
    }

    showDownloadNotification({
      type: 'error',
      filename,
      message: message || `Error al descargar ${filename}. Por favor, inténtalo de nuevo.`,
      autoCloseDelay
    });
  }, [showDownloadNotification]);

  /**
   * Hide the current download notification manually
   */
  const hide = useCallback(() => {
    hideDownloadNotification();
  }, [hideDownloadNotification]);

  /**
   * Show a generic download notification with full control
   * @param {Object} options - Notification options
   * @param {'success'|'error'} options.type - Type of notification
   * @param {string} options.filename - The filename
   * @param {string} [options.message] - Custom message
   * @param {number} [options.autoCloseDelay] - Auto-close delay
   */
  const show = useCallback((options) => {
    const { type, filename, message = '', autoCloseDelay = 3000 } = options || {};

    if (!type || !['success', 'error'].includes(type)) {
      throw new Error('type is required and must be either "success" or "error"');
    }

    if (!filename || typeof filename !== 'string') {
      throw new Error('filename is required and must be a string');
    }

    showDownloadNotification({
      type,
      filename,
      message,
      autoCloseDelay
    });
  }, [showDownloadNotification]);

  return {
    showSuccess,
    showError,
    hide,
    show
  };
};

export default useDownloadNotification;