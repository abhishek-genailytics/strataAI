'use client';
import { createContext, useContext, useState, PropsWithChildren } from 'react';

type OrgContextShape = { 
  orgId: string | null; 
  setOrgId: (id: string | null) => void; 
};

const OrgContext = createContext<OrgContextShape>({ 
  orgId: null, 
  setOrgId: () => {} 
});

export function OrgProvider({ children }: PropsWithChildren) {
  const [orgId, setOrgId] = useState<string | null>(null);
  return (
    <OrgContext.Provider value={{ orgId, setOrgId }}>
      {children}
    </OrgContext.Provider>
  );
}

export function useOrg() { 
  return useContext(OrgContext); 
}
