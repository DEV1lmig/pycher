import { useState, useEffect } from 'react';
import { UAParser } from 'ua-parser-js';

/**
 * Hook to check if the user is on an unsupported mobile or tablet device.
 * @returns {boolean} - True if the device is unsupported, false otherwise.
 */
export function useDeviceCheck() {
  const [isUnsupported, setIsUnsupported] = useState(false);

  useEffect(() => {
    // This check runs only once on the client-side.
    const parser = new UAParser(navigator.userAgent);
    const device = parser.getDevice();

    // We consider 'mobile' and 'tablet' devices as unsupported.
    if (device.type === 'mobile' || device.type === 'tablet') {
      setIsUnsupported(true);
    }
  }, []);

  return isUnsupported;
}
