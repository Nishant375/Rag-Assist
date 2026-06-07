import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { useChatRouteChatPost } from "@/api/generated/chat/chat";
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
  isPending: boolean;
  send: (text: string) => Promise<void>;
  clear: () => void;
}

const STORAGE_KEY = "chat:messages";

function load(): ChatMessage[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
  } catch {
    return [];
  }
}

function save(messages: ChatMessage[]) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  } catch {
    /* sessionStorage unavailable — non-fatal */
  }
}

const ChatContext = createContext<ChatState | null>(null);

// Lives above the router outlet, so chat history survives tab switches and
// page reloads (sessionStorage) instead of being wiped when ChatPage unmounts.
export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>(load);
  const chat = useChatRouteChatPost();

  const append = useCallback((msg: ChatMessage) => {
    setMessages((prev) => {
      const next = [...prev, msg];
      save(next);
      return next;
    });
  }, []);

  const send = useCallback(
    async (text: string) => {
      const message = text.trim();
      if (!message || chat.isPending) return;
      append({ role: "user", content: message });
      try {
        const res = (await chat.mutateAsync({ data: { message } })) as ChatResponse;
        append({ role: "assistant", content: res.answer, rewritten: res.rewritten_question });
      } catch (err) {
        append({ role: "assistant", content: `Something went wrong: ${getErrorMessage(err, "Request failed")}`, error: true });
      }
    },
    [append, chat]
  );

  const clear = useCallback(() => {
    setMessages([]);
    save([]);
  }, []);

  return (
    <ChatContext.Provider value={{ messages, isPending: chat.isPending, send, clear }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat(): ChatState {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
