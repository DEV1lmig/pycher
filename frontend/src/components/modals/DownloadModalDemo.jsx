import React, { useState } from 'react';
import DownloadModal from './DownloadModal';
import { Button } from '@/components/ui/button';

const DownloadModalDemo = () => {
  const [modalState, setModalState] = useState({
    isOpen: false,
    type: 'success',
    filename: '',
    message: ''
  });

  const showSuccessModal = () => {
    setModalState({
      isOpen: true,
      type: 'success',
      filename: 'manual_de_usuario_pycher.pdf',
      message: 'Tu archivo se ha descargado correctamente.'
    });
  };

  const showErrorModal = () => {
    setModalState({
      isOpen: true,
      type: 'error',
      filename: 'reporte_progreso.pdf',
      message: 'No se pudo descargar el archivo. Por favor, inténtalo de nuevo.'
    });
  };

  const showSuccessWithAutoClose = () => {
    setModalState({
      isOpen: true,
      type: 'success',
      filename: 'documento_ejemplo.pdf',
      message: 'Descarga exitosa con cierre automático en 5 segundos.'
    });
  };

  const closeModal = () => {
    setModalState(prev => ({ ...prev, isOpen: false }));
  };

  return (
    <div className="p-8 space-y-4 bg-[#160f30] min-h-screen">
      <h1 className="text-2xl font-bold text-white mb-6">DownloadModal Demo</h1>
      
      <div className="space-y-4">
        <Button onClick={showSuccessModal} className="mr-4">
          Show Success Modal
        </Button>
        
        <Button onClick={showErrorModal} variant="destructive" className="mr-4">
          Show Error Modal
        </Button>
        
        <Button onClick={showSuccessWithAutoClose} variant="secondary">
          Success with Auto-close (5s)
        </Button>
      </div>

      <div className="mt-8 text-gray-300 space-y-2">
        <h2 className="text-lg font-semibold">Test Instructions:</h2>
        <ul className="list-disc list-inside space-y-1 text-sm">
          <li>Click buttons to test different modal states</li>
          <li>Test ESC key to close modal</li>
          <li>Test clicking backdrop to close modal</li>
          <li>Test keyboard navigation (Tab key)</li>
          <li>Test auto-close functionality</li>
          <li>Test user interaction canceling auto-close</li>
        </ul>
      </div>

      <DownloadModal
        isOpen={modalState.isOpen}
        onClose={closeModal}
        type={modalState.type}
        filename={modalState.filename}
        message={modalState.message}
        autoCloseDelay={modalState.message.includes('5 segundos') ? 5000 : 3000}
      />
    </div>
  );
};

export default DownloadModalDemo;