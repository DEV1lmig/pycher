import React from 'react';
import { useCongratsModal } from '@/context/CongratsModalContext';
import { useNavigate } from '@tanstack/react-router';

export default function AllCoursesCompletedModal() {
  const { closeCongratsModal } = useCongratsModal();
  const navigate = useNavigate();

  const handleClose = () => {
    closeCongratsModal();
    navigate({ to: '/home' }); // Navega al dashboard
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-primary-opaque text-white rounded-lg shadow-2xl p-8 max-w-md text-center border border-green-500">
        <h2 className="text-3xl font-bold text-green-400 mb-4">¡ENHORABUENA!</h2>
        <p className="text-base mb-6">
          Has completado todos los cursos disponibles. ¡Has demostrado una increíble dedicación y has dominado los fundamentos de Python!
        </p>
        <button
          onClick={handleClose}
          className="bg-green-400 hover:bg-green-600 text-white font-bold py-2 px-6 rounded-lg"
        >
          Ir al Dashboard
        </button>
      </div>
    </div>
  );
}
