import React, { useState } from 'react';
import DownloadModal from '../modals/DownloadModal';
import { Button } from '@/components/ui/button';

const ResponsiveDownloadModalTest = () => {
  const [modalState, setModalState] = useState({
    isOpen: false,
    type: 'success',
    filename: '',
    message: ''
  });

  const showModal = (type, filename, message) => {
    setModalState({
      isOpen: true,
      type,
      filename,
      message
    });
  };

  const closeModal = () => {
    setModalState(prev => ({ ...prev, isOpen: false }));
  };

  const testCases = [
    {
      label: 'Success - Short filename',
      type: 'success',
      filename: 'report.pdf',
      message: 'Tu archivo se ha descargado correctamente.'
    },
    {
      label: 'Success - Long filename',
      type: 'success',
      filename: 'very-long-filename-that-should-wrap-properly-on-mobile-devices-and-test-responsive-behavior.pdf',
      message: 'Tu archivo con nombre muy largo se ha descargado correctamente.'
    },
    {
      label: 'Error - Network issue',
      type: 'error',
      filename: 'failed-download.pdf',
      message: 'No se pudo conectar al servidor. Por favor, verifica tu conexión a internet e intenta nuevamente.'
    },
    {
      label: 'Success - No custom message',
      type: 'success',
      filename: 'manual-usuario.pdf',
      message: ''
    },
    {
      label: 'Error - No filename',
      type: 'error',
      filename: '',
      message: 'Error desconocido al procesar la descarga.'
    }
  ];

  return (
    <div className="min-h-screen bg-[#160f30] p-4 sm:p-6 md:p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-6 sm:mb-8">
          Responsive Download Modal Test
        </h1>
        
        <div className="bg-[#1a1433] border border-[#312a56] rounded-xl p-4 sm:p-6 mb-6 sm:mb-8">
          <h2 className="text-lg sm:text-xl font-semibold text-white mb-4">
            Test Instructions
          </h2>
          <div className="text-gray-300 text-sm sm:text-base space-y-2 leading-relaxed">
            <p>• Test each modal type on different screen sizes</p>
            <p>• Verify touch targets are at least 44px on mobile</p>
            <p>• Check that text remains readable on all screen sizes</p>
            <p>• Ensure modal positioning works correctly (bottom sheet on mobile, centered on desktop)</p>
            <p>• Test backdrop click and ESC key dismissal</p>
            <p>• Verify animations are smooth and respect reduced motion preferences</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-6 sm:mb-8">
          {testCases.map((testCase, index) => (
            <Button
              key={index}
              onClick={() => showModal(testCase.type, testCase.filename, testCase.message)}
              className={`
                p-3 sm:p-4 h-auto text-left justify-start
                ${testCase.type === 'success' 
                  ? 'bg-green-600 hover:bg-green-700 text-white' 
                  : 'bg-red-600 hover:bg-red-700 text-white'
                }
                min-h-[44px] touch-manipulation
              `}
            >
              <div>
                <div className="font-medium text-sm sm:text-base mb-1">
                  {testCase.label}
                </div>
                <div className="text-xs opacity-80 truncate">
                  {testCase.filename || 'No filename'}
                </div>
              </div>
            </Button>
          ))}
        </div>

        <div className="bg-[#1a1433] border border-[#312a56] rounded-xl p-4 sm:p-6">
          <h2 className="text-lg sm:text-xl font-semibold text-white mb-4">
            Screen Size Information
          </h2>
          <div className="text-gray-300 text-sm sm:text-base space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-1 sm:space-y-0">
              <span className="font-medium">Current viewport:</span>
              <span className="font-mono text-green-400">
                {typeof window !== 'undefined' ? `${window.innerWidth}x${window.innerHeight}` : 'Loading...'}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-4">
              <div>
                <span className="font-medium">Breakpoints:</span>
                <ul className="text-xs mt-1 space-y-1">
                  <li>• Mobile: &lt; 640px</li>
                  <li>• Tablet: 640px - 768px</li>
                  <li>• Desktop: &gt; 768px</li>
                </ul>
              </div>
              <div>
                <span className="font-medium">Modal behavior:</span>
                <ul className="text-xs mt-1 space-y-1">
                  <li>• Mobile: Bottom sheet</li>
                  <li>• Tablet+: Centered</li>
                  <li>• Touch targets: 44px min</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <DownloadModal
        isOpen={modalState.isOpen}
        onClose={closeModal}
        type={modalState.type}
        filename={modalState.filename}
        message={modalState.message}
        autoCloseDelay={5000} // Longer delay for testing
      />
    </div>
  );
};

export default ResponsiveDownloadModalTest;