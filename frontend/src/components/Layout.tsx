import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/Button";
import { useHealthHealthGet } from "@/api/generated/public/public";

const TABS = [
  { to: "/chat", label: "💬 Chat" },
  { to: "/documents", label: "📂 Documents" },
  { to: "/knowledge-base", label: "🗂️ Knowledge Base" },
];

export function Layout() {
  const { email, signOut } = useAuth();
  const health = useHealthHealthGet({
    query: { refetchInterval: 30_000, retry: false },
  });
  const online = health.isSuccess;

  return (
    <div className="mx-auto flex h-screen max-w-[1000px] flex-col px-6">
      <header className="flex flex-shrink-0 items-center justify-between border-b border-panel py-4">
        <div className="flex items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-[10px] bg-gradient-to-br from-indigo-500 to-violet-500 text-lg">
            ⚡
          </div>
          <div>
            <div className="text-[15px] font-bold text-gray-50">Rag-Assist</div>
            <div className="text-[11px] text-faint">Chat with your documents using AI</div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="inline-flex items-center gap-1.5 text-[11px] text-faint">
            <span className={`h-[7px] w-[7px] rounded-full ${online ? "bg-green-500" : "bg-red-500"}`} />
            {online ? "Connected" : "API offline"}
          </span>
          <span className="text-xs text-faint">{email}</span>
          <Button onClick={signOut}>Sign out</Button>
        </div>
      </header>

      <nav className="flex flex-shrink-0 gap-1 border-b border-panel">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            className={({ isActive }) => `tab ${isActive ? "tab-active" : ""}`}
          >
            {t.label}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  );
}
