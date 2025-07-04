import { useState, useEffect } from 'react';

/**
 * Hook to check if the user is on an unsupported mobile or tablet device.
 * @returns {boolean} - True if the device is unsupported, false otherwise.
 */
export function useDeviceCheck() {
  const [isUnsupported, setIsUnsupported] = useState(false);

  useEffect(() => {
    // This check runs only once on the client-side.
    const userAgent = navigator.userAgent;
    const isMobileOrTablet = /Mobi|Android|iPhone|iPad|iPod|Tablet/i.test(userAgent);

    // We consider any device that identifies as mobile/tablet as unsupported.
    // You could also add a width check like `window.innerWidth < 1024`
    // but the user agent is generally sufficient for this purpose.
    if (isMobileOrTablet) {
      setIsUnsupported(true);
    }
  }, []);

  return isUnsupported;
}
