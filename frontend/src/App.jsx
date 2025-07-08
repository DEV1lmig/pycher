import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { RouterProvider } from '@tanstack/react-router';
import { queryClient } from './services/api';
import { router } from './router';
import { Toaster } from 'react-hot-toast';
import { useDeviceCheck } from './hooks/useDeviceCheck';
import UnsupportedDevicePage from './pages/UnsupportedDevicePage';
import './App.css';

function App() {
  const isUnsupportedDevice = useDeviceCheck();

  if (isUnsupportedDevice) {
    return <UnsupportedDevicePage />;
  }

  return (
    <QueryClientProvider client={queryClient}>
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
    </QueryClientProvider>
  );
}

export default App;
