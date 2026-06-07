import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import {
  useLoginRouteAuthLoginPost,
  useSignupRouteAuthSignupPost,
} from "@/api/generated/auth/auth";
import type { LoginResponse } from "@/lib/types";

type Mode = "login" | "signup";

export function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const login = useLoginRouteAuthLoginPost();
  const signup = useSignupRouteAuthSignupPost();
  const busy = login.isPending || signup.isPending;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!email || !password) return setError("Enter email and password.");
    if (mode === "signup" && password.length < 6)
      return setError("Password must be at least 6 characters.");

    try {
      if (mode === "login") {
        const res = (await login.mutateAsync({ data: { email, password } })) as LoginResponse;
        signIn(res.access_token, res.user?.email ?? email);
        navigate("/chat", { replace: true });
      } else {
        await signup.mutateAsync({ data: { email, password } });
        setSuccess("Account created! You can log in now.");
        setMode("login");
      }
    } catch {
      setError(mode === "login" ? "Invalid email or password." : "Signup failed.");
    }
  }

  return (
    <div className="grid min-h-screen place-items-center p-6">
      <div className="w-full max-w-[400px]">
        <div className="mb-7 text-center">
          <div className="inline-flex items-center gap-2.5">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-xl">
              ⚡
            </div>
            <h1 className="text-[22px] font-bold text-slate-100">Rag-Assist</h1>
          </div>
          <p className="mt-2 text-[13px] text-muted">Chat with your documents using AI</p>
        </div>

        <div className="mb-5 flex gap-1 border-b border-panel">
          <button
            type="button"
            className={`tab ${mode === "login" ? "tab-active" : ""}`}
            onClick={() => { setMode("login"); setError(""); }}
          >
            Login
          </button>
          <button
            type="button"
            className={`tab ${mode === "signup" ? "tab-active" : ""}`}
            onClick={() => { setMode("signup"); setError(""); }}
          >
            Sign up
          </button>
        </div>

        {error && (
          <div className="mb-3.5 rounded-lg border border-red-900 bg-red-950/60 px-3.5 py-2.5 text-[13px] text-red-300">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-3.5 rounded-lg border border-green-900 bg-green-950/60 px-3.5 py-2.5 text-[13px] text-green-300">
            {success}
          </div>
        )}

        <form onSubmit={submit}>
          <Input
            id="email"
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            id="password"
            label={mode === "signup" ? "Password (min 6 chars)" : "Password"}
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit" variant="primary" block loading={busy}>
            {mode === "login" ? "Login →" : "Create account"}
          </Button>
        </form>
      </div>
    </div>
  );
}
