import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

interface AuthState {
  token: string | null;
  email: string | null;
  signIn: (token: string, email: string) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));
  const [email, setEmail] = useState<string | null>(() => localStorage.getItem("email"));

  const signIn = useCallback((newToken: string, newEmail: string) => {
    localStorage.setItem("token", newToken);
    localStorage.setItem("email", newEmail ?? "");
    setToken(newToken);
    setEmail(newEmail ?? "");
  }, []);

  const signOut = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    sessionStorage.removeItem("chat:messages");
    setToken(null);
    setEmail(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, email, signIn, signOut }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
