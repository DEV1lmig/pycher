import React from 'react';
import { useDownloadNotification } from '../../hooks/useDownloadNotification';
import { Button } from '../ui/button';

/**
 * Test component to verify DownloadNotificationProvider integration
 * This component should be able to access the download notification context
 * and trigger success/error notifications
 */
const DownloadNotificationTest = () => {
  const { showSuccess, showError, hide } = useDownloadNotification();

  const handleTestSuccess = () => {
    showSuccess('test-document.pdf', 'Test success notification');
  };

  const handleTestError = () => {
    showError('failed-document.pdf', 'Test error notification');
  };

  const handleHide = () => {
    hide();
  };

  return (
    <div className="p-4 space-y-4 bg-[#1a1433] border border-[#312a56] rounded-lg">
      <h3 className="text-white text-lg font-semibold">Download Notification Test</h3>
      <p className="text-gray-300 text-sm">
        Use these buttons to test the download notification system integration.
      </p>
      <div className="flex space-x-2">
        <Button onClick={handleTestSuccess} variant="default">
          Test Success
        </Button>
        <Button onClick={handleTestError} variant="destructive">
          Test Error
        </Button>
        <Button onClick={handleHide} variant="outline">
          Hide Modal
        </Button>
      </div>
    </div>
  );
};

export default DownloadNotificationTest;