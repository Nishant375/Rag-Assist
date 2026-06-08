import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useChatStore } from "./chat";
import { useIngestStore } from "./ingest";

interface AuthState {
  token: string | null;
  email: string | null;
  signIn: (token: string, email: string) => void;
  signOut: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      email: null,
      signIn: (token, email) => set({ token, email }),
      signOut: () => {
        // Clear per-user client state too.
        useChatStore.getState().clear();
        useIngestStore.getState().reset();
        set({ token: null, email: null });
      },
    }),
    { name: "auth" }
  )
);
