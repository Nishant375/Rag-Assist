import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { useChatRouteChatPost } from "@/api/generated/chat/chat";
import type { ChatResponse } from "@/api/generated/model";
import { getErrorMessage } from "@/lib/error";

interface Message {
  role: "user" | "assistant";
  content: string;
  rewritten?: string | null;
  error?: boolean;
}

const SUGGESTIONS = ["Hi!", "What can you help me with?", "Summarize my documents", "What topics are covered?"];

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const chat = useChatRouteChatPost();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chat.isPending]);

  async function send(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || chat.isPending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg }]);
    try {
      const res = (await chat.mutateAsync({ data: { message: msg } })) as ChatResponse;
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, rewritten: res.rewritten_question },
      ]);
    } catch (err) {
      const detail = getErrorMessage(err, "Request failed");
      setMessages((m) => [...m, { role: "assistant", content: `Something went wrong: ${detail}`, error: true }]);
    }
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto py-5">
        {messages.length === 0 ? (
          <div className="px-5 py-14 text-center text-faint">
            <div className="mb-4 text-[44px]">⚡</div>
            <h2 className="mb-2 text-xl font-semibold text-gray-50">Ask me anything</h2>
            <p className="mx-auto mb-6 max-w-[380px] text-sm leading-relaxed text-muted">
              Chat freely — or upload documents in the <b>Documents</b> tab and I'll answer from them.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-border bg-panel px-3.5 py-1.5 text-xs text-muted transition hover:border-brand hover:text-indigo-300"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`mb-3.5 flex ${m.role === "user" ? "justify-end" : ""}`}>
              <div className="max-w-[78%]">
                <div
                  className={`whitespace-pre-wrap break-words px-4 py-2.5 leading-relaxed ${
                    m.role === "user"
                      ? "rounded-[18px_18px_4px_18px] bg-indigo-900 text-indigo-100"
                      : "rounded-[18px_18px_18px_4px] bg-panel text-gray-200"
                  }`}
                >
                  {m.content}
                </div>
                {m.role === "assistant" && !m.error && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    <span className="rounded-lg border border-blue-900 bg-blue-950 px-2 py-0.5 text-[10px] font-medium text-blue-400">
                      🌐 API
                    </span>
                    {m.rewritten && (
                      <span className="rounded-lg border border-violet-900 bg-violet-950 px-2 py-0.5 text-[10px] font-medium text-violet-400">
                        ✏️ rewritten
                      </span>
                    )}
                  </div>
                )}
                {m.rewritten && (
                  <div className="mt-1.5 rounded-lg border border-violet-900 bg-violet-950 px-2.5 py-1.5 text-xs text-violet-400">
                    <b>Rewritten to:</b> {m.rewritten}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {chat.isPending && (
          <div className="mb-3.5 flex">
            <div className="rounded-[18px_18px_18px_4px] bg-panel px-4 py-2.5">
              <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-indigo-400/40 border-t-indigo-400" />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="flex flex-shrink-0 gap-2 border-t border-panel py-3 pb-4">
        <input
          className="input rounded-2xl"
          placeholder="Ask anything …"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={chat.isPending}
        />
        <button
          onClick={() => send()}
          disabled={chat.isPending || !input.trim()}
          aria-label="Send"
          className="w-11 flex-shrink-0 rounded-xl bg-brand text-lg text-white transition hover:bg-brand-hover disabled:opacity-50"
        >
          ↑
        </button>
      </div>
    </div>
  );
}
