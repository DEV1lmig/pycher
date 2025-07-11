import React, { createContext, useState, useContext, useMemo } from 'react';

const CongratsModalContext = createContext(null);

export function CongratsModalProvider({ children }) {
  const [isCongratsModalOpen, setIsCongratsModalOpen] = useState(false);

  const openCongratsModal = () => setIsCongratsModalOpen(true);
  const closeCongratsModal = () => setIsCongratsModalOpen(false);

  const value = useMemo(() => ({
    isCongratsModalOpen,
    openCongratsModal,
    closeCongratsModal,
  }), [isCongratsModalOpen]);

  return (
    <CongratsModalContext.Provider value={value}>
      {children}
    </CongratsModalContext.Provider>
  );
}

export function useCongratsModal() {
  const context = useContext(CongratsModalContext);
  if (!context) {
    throw new Error('useCongratsModal debe ser usado dentro de un CongratsModalProvider');
  }
  return context;
}
