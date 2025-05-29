import { useEffect, useState } from "react";
import { getUserProfile, downloadProgressReport } from "@/services/userService"; // Import downloadProgressReport
import AnimatedContent from '../ui/animated-content';
import Particles from "../ui/particles";
// Consider adding a toast notification library for better UX, e.g., react-hot-toast
// import toast from 'react-hot-toast';

export function WelcomeHeader() {
  const [user, setUser] = useState(null);
  const [isDownloadingReport, setIsDownloadingReport] = useState(false);
  const [reportError, setReportError] = useState(null);

  useEffect(() => {
    getUserProfile().then(setUser).catch(err => {
      console.error("Failed to fetch user profile:", err);
      // Handle error fetching user profile if necessary
    });
  }, []);

  const handleDownloadReport = async () => {
    setIsDownloadingReport(true);
    setReportError(null);
    try {
      const result = await downloadProgressReport();
      if (result.success) {
        // Optionally, show a success message
        // For example, using react-hot-toast: toast.success(`Report "${result.filename}" downloaded!`);
        alert(`Report "${result.filename}" download initiated!`);
      }
    } catch (error) {
      console.error("Download failed:", error);
      setReportError(error.message || "An unknown error occurred while downloading the report.");
      // For example, using react-hot-toast: toast.error(error.message || "Failed to download report.");
      alert(`Failed to download report: ${error.message}`);
    } finally {
      setIsDownloadingReport(false);
    }
  };

  return (
    <AnimatedContent
      distance={40}
      direction="vertical"
      reverse={true}
      config={{ tension: 100, friction: 10 }}
      initialOpacity={0.2}
      animateOpacity
      scale={1}
      threshold={0.2}
    >
      <div className="bg-dark shadow-2xl border-primary/5 border py-12 relative overflow-hidden rounded-lg p-6 cursor-default">
        <div className="absolute inset-0 z-10">
          <Particles
            particleColors={['#8363f2', '#8363f2']}
            particleCount={300}
            particleSpread={5}
            speed={0.3}
            particleBaseSize={70}
            moveParticlesOnHover={true}
            alphaParticles={false}
            disableRotation={true}
          />
        </div>
        <div className="relative z-0">
          <h1 className="text-3xl font-bold mb-2  relative text-white">
            ¡Bienvenido(a) de vuelta, {user ? `${user.first_name || user.username}` : "Usuario"}!
          </h1>
          <p className="text-gray-300 mb-4">
            Continúa tu viaje de aprendizaje en Python. {/* You might want to fetch actual course progress count here */}
          </p>
        </div>
        <div className="inline-flex flex-wrap gap-4 relative z-10 mt-4">
          <button className="bg-primary hover:bg-primary-opaque transition ease-out duration-300 text-white px-4 py-2 rounded-md flex items-center">
            Continuar aprendiendo {/* This button's functionality is not part of this request */}
          </button>
          <button
            className="bg-secondary text-dark px-4 py-2 rounded-md hover:bg-secondary hover:text-dark transition ease-out duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleDownloadReport}
            disabled={isDownloadingReport}
          >
            {isDownloadingReport ? 'Generando PDF...' : 'Ver mi progreso'}
          </button>
        </div>
        {reportError && (
          <p className="text-red-500 mt-2 relative z-10 text-sm">{reportError}</p>
        )}
      </div>
    </AnimatedContent>
  );
}
