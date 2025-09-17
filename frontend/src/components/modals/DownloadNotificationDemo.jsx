import React from 'react';
import { useDownloadNotification } from '../../hooks/useDownloadNotification';

/**
 * Demo component to test the useDownloadNotification hook
 * This component can be used to verify the hook functionality
 */
const DownloadNotificationDemo = () => {
  const { showSuccess, showError, hide, show } = useDownloadNotification();

  const handleShowSuccess = () => {
    showSuccess('reporte-progreso.pdf', 'Tu reporte se ha descargado correctamente');
  };

  const handleShowError = () => {
    showError('manual-usuario.pdf', 'No se pudo descargar el archivo. Verifica tu conexión.');
  };

  const handleShowCustom = () => {
    show({
      type: 'success',
      filename: 'documento-personalizado.pdf',
      message: 'Descarga personalizada completada',
      autoCloseDelay: 5000
    });
  };

  const handleHide = () => {
    hide();
  };

  return (
    <div className="p-6 bg-[#1a1433] border border-[#312a56] rounded-lg max-w-md mx-auto">
      <h3 className="text-white text-lg font-semibold mb-4">
        Download Notification Hook Demo
      </h3>
      
      <div className="space-y-3">
        <button
          onClick={handleShowSuccess}
          className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
        >
          Show Success Notification
        </button>
        
        <button
          onClick={handleShowError}
          className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
        >
          Show Error Notification
        </button>
        
        <button
          onClick={handleShowCustom}
          className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
        >
          Show Custom Notification
        </button>
        
        <button
          onClick={handleHide}
          className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
        >
          Hide Notification
        </button>
      </div>
      
      <div className="mt-4 text-sm text-gray-300">
        <p>Use these buttons to test the useDownloadNotification hook functionality:</p>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li>Success: Shows green notification with checkmark</li>
          <li>Error: Shows red notification with error icon</li>
          <li>Custom: Shows notification with custom settings</li>
          <li>Hide: Manually dismisses current notification</li>
        </ul>
      </div>
    </div>
  );
};

export default DownloadNotificationDemo;