"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "agent3-access-token";

type TokenContextValue = {
  token: string | null;
  setToken: (value: string | null) => void;
};

const TokenContext = createContext<TokenContextValue | undefined>(undefined);

export function TokenProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setTokenState(stored);
    }
  }, []);

  const setToken = useCallback((value: string | null) => {
    setTokenState(value);
    if (value) {
      window.localStorage.setItem(STORAGE_KEY, value);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const value = useMemo(() => ({ token, setToken }), [token, setToken]);

  return <TokenContext.Provider value={value}>{children}</TokenContext.Provider>;
}

export function useAuthToken() {
  const ctx = useContext(TokenContext);
  if (!ctx) {
    throw new Error("useAuthToken must be used within a TokenProvider");
  }
  return ctx;
}
