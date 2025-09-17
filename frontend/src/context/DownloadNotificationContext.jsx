import React, { createContext, useContext, useState, useCallback, useRef, useEffect, useMemo } from 'react';
import PropTypes from 'prop-types';

// Create the context
const DownloadNotificationContext = createContext({
  showDownloadNotification: ({ type, filename, message }) => {},
  hideDownloadNotification: () => {}
});

// Provider component
export const DownloadNotificationProvider = ({ children }) => {
  const [notificationState, setNotificationState] = useState({
    isVisible: false,
    type: null, // 'success' | 'error' | null
    filename: '',
    message: '',
  });

  // Use ref to store timer so it persists across re-renders
  const autoCloseTimerRef = useRef(null);

  // Clear existing timer
  const clearTimer = useCallback(() => {
    if (autoCloseTimerRef.current) {
      clearTimeout(autoCloseTimerRef.current);
      autoCloseTimerRef.current = null;
    }
  }, []);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      clearTimer();
    };
  }, [clearTimer]);

  // Hide notification function
  const hideDownloadNotification = useCallback(() => {
    clearTimer();
    setNotificationState({
      isVisible: false,
      type: null,
      filename: '',
      message: '',
    });
  }, [clearTimer]);

  // Show notification function
  const showDownloadNotification = useCallback(({ type, filename, message = '', autoCloseDelay = 3000 }) => {
    // Clear any existing timer first
    clearTimer();

    // Prevent multiple modals by hiding current one first
    setNotificationState({
      isVisible: true,
      type,
      filename,
      message,
    });

    // Set up auto-dismiss timer if delay is provided
    if (autoCloseDelay > 0) {
      autoCloseTimerRef.current = setTimeout(() => {
        hideDownloadNotification();
      }, autoCloseDelay);
    }
  }, [clearTimer, hideDownloadNotification]);

  // Context value with useMemo for optimization
  const contextValue = useMemo(() => ({
    ...notificationState,
    showDownloadNotification,
    hideDownloadNotification
  }), [notificationState, showDownloadNotification, hideDownloadNotification]);

  return (
    <DownloadNotificationContext.Provider value={contextValue}>
      {children}
    </DownloadNotificationContext.Provider>
  );
};

DownloadNotificationProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

// Custom hook to use the context
export const useDownloadNotificationContext = () => {
  const context = useContext(DownloadNotificationContext);
  
  if (!context) {
    throw new Error('useDownloadNotificationContext must be used within a DownloadNotificationProvider');
  }
  
  return context;
};

export default DownloadNotificationContext;