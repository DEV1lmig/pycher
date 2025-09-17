import { TabletSmartphone, Monitor } from 'lucide-react';
import logo from '@/assets/img/logo-pycher.png';

export default function UnsupportedDevicePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#160f30] text-white p-6 text-center">
      <img src={logo} alt="Pycher Logo" className="w-48 mb-8" />
      <div className="flex items-center justify-center p-6 bg-primary/10 rounded-full mb-6">
        <TabletSmartphone className="h-16 w-16 text-primary" />
      </div>
      <h1 className="text-3xl font-bold text-white mb-3">Dispositivo no compatible</h1>
      <p className="text-lg text-gray-300 max-w-md">
        Pycher está optimizado para una experiencia de escritorio. Para acceder a todas las funcionalidades, por favor, utiliza un ordenador.
      </p>
      <div className="mt-8 flex items-center gap-3 text-gray-400">
        <Monitor className="h-6 w-6" />
        <span>Recomendado: Vista de escritorio</span>
      </div>
    </div>
  );
}