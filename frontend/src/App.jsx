import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { RouterProvider } from '@tanstack/react-router';
import { queryClient } from './services/api';
import { router } from './router';
import { Toaster } from 'react-hot-toast';
import { useDeviceCheck } from './hooks/useDeviceCheck';
import UnsupportedDevicePage from './pages/UnsupportedDevicePage';
import { CongratsModalProvider, useCongratsModal } from './context/CongratsModalContext'; // 1. Importar
import AllCoursesCompletedModal from './components/modals/AllCoursesCompletedModal'; // 2. Importar
import './App.css';

// 3. Crear un componente interno para acceder al contexto
function AppContent() {
  const isUnsupportedDevice = useDeviceCheck();
  const { isCongratsModalOpen } = useCongratsModal();

  if (isUnsupportedDevice) {
    return <UnsupportedDevicePage />;
  }

  return (
    <>
      <Toaster
        position="top-right"
        reverseOrder={false}
        toastOptions={{
          className: 'bg-[#1a1433] text-white border-[#312a56]',
          duration: 3000,
          style: {
            background: '#1a1433',
            color: '#fff',
            border: '1px solid #312a56',
          },
        }}
      />
      <RouterProvider router={router} />
      <ReactQueryDevtools initialIsOpen={false} />

      {/* 4. Renderizar el modal aquí */}
      {isCongratsModalOpen && <AllCoursesCompletedModal />}
    </>
  );
}

// 5. Envolver el contenido con el proveedor
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <CongratsModalProvider>
        <AppContent />
      </CongratsModalProvider>
    </QueryClientProvider>
  );
}

export default App;
