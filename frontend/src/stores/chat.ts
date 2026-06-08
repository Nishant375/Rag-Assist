import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { chatRouteChatPost } from "@/api/generated/chat/chat";
import type { ChatResponse } from "@/api/generated/model";
import { getErrorMessage } from "@/lib/error";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  rewritten?: string | null;
  error?: boolean;
}

interface ChatState {
  messages: ChatMessage[];
  sending: boolean;
  send: (text: string) => Promise<void>;
  clear: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      sending: false,
      send: async (text) => {
        const msg = text.trim();
        if (!msg || get().sending) return;
        set((s) => ({ messages: [...s.messages, { role: "user", content: msg }], sending: true }));
        try {
          const res = (await chatRouteChatPost({ message: msg })) as ChatResponse;
          set((s) => ({
            messages: [...s.messages, { role: "assistant", content: res.answer, rewritten: res.rewritten_question }],
            sending: false,
          }));
        } catch (err) {
          set((s) => ({
            messages: [...s.messages, { role: "assistant", content: `Something went wrong: ${getErrorMessage(err, "Request failed")}`, error: true }],
            sending: false,
          }));
        }
      },
      clear: () => set({ messages: [] }),
    }),
    { name: "chat", storage: createJSONStorage(() => sessionStorage), partialize: (s) => ({ messages: s.messages }) }
  )
);
