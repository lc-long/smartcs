import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useChatStore } from "../../store/chatStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useAuth } from "../../contexts/AuthContext";
import type { WSEvent } from "../../types";
import MessageBubble from "./MessageBubble";
import { Send, Package, CreditCard, RotateCcw, Wrench, FileText, Phone, Sparkles, Loader2 } from "lucide-react";

const AGENT_LABELS: Record<string, string> = { billing: "billing", technical: "techSupport", refund: "refund", general: "general", escalation: "human", supervisor: "smartRouter" };

export default function ChatWindow() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const customerId = user?.customer_id || `guest-${user?.id?.slice(0, 8) || "unknown"}`;
  const [conversationId] = useState(() => crypto.randomUUID());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, addMessage, isProcessing, setProcessing, currentAgent, setCurrentAgent, addEvent } = useChatStore();
  const { connected, sendMessage } = useWebSocket({ conversationId, customerId, onEvent: handleEvent });

  function handleEvent(event: WSEvent) {
    addEvent(event);
    switch (event.type) {
      case "planning": if (event.status === "analyzing") { setCurrentAgent("supervisor"); setProcessing(true); } break;
      case "complex_task_start": case "parallel_start": setCurrentAgent("supervisor"); setProcessing(true); break;
      case "subtask_start": setCurrentAgent(event.agent as string); break;
      case "agent_start": setCurrentAgent(event.agent as string); setProcessing(true); break;
      case "agent_response": addMessage({ id: crypto.randomUUID(), role: "assistant", content: event.content as string, agent_name: event.agent as string, tools_called: [], created_at: new Date().toISOString() }); setProcessing(false); setCurrentAgent(null); break;
      case "error": addMessage({ id: crypto.randomUUID(), role: "system", content: event.message as string, tools_called: [], created_at: new Date().toISOString() }); setProcessing(false); setCurrentAgent(null); break;
      case "human_approval_needed": addMessage({ id: crypto.randomUUID(), role: "system", content: `[${t("chat.needsApproval")}] ${event.reason}`, tools_called: [], created_at: new Date().toISOString() }); break;
    }
  }

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const handleSend = (text?: string) => {
    const msg = text || input.trim();
    if (!msg || isProcessing) return;
    addMessage({ id: crypto.randomUUID(), role: "user", content: msg, tools_called: [], created_at: new Date().toISOString() });
    sendMessage(msg);
    setInput("");
  };

  const QUICK = [
    { label: t("chat.myOrders"), question: "Show me my orders", icon: Package },
    { label: t("chat.billing"), question: "Check my billing", icon: CreditCard },
    { label: t("chat.refund"), question: "I want to request a refund", icon: RotateCcw },
    { label: t("chat.techSupport"), question: "My device has an issue", icon: Wrench },
    { label: t("chat.refundPolicy"), question: "What is your refund policy?", icon: FileText },
    { label: t("chat.contact"), question: "What is your customer service number?", icon: Phone },
  ];

  const agentLabel = currentAgent ? t(`agent.${AGENT_LABELS[currentAgent] || "general"}`) : "";

  return (
    <div className="flex flex-col h-full" style={{ background: "var(--bg-app)" }}>
      <header className="h-12 px-5 flex items-center justify-between flex-shrink-0"
        style={{ background: "var(--bg-app)", borderBottom: "1px solid var(--border-subtle)" }}>
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4" style={{ color: "var(--accent)" }} />
          <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{t("chat.title")}</h1>
          <div className="flex items-center gap-1 ml-2">
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: connected ? "var(--success)" : "var(--warning)" }} />
            <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{connected ? t("chat.connected") : t("chat.connecting")}</span>
          </div>
        </div>
        {isProcessing && agentLabel && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium"
            style={{ background: "var(--badge-bg)", color: "var(--accent)", border: "1px solid var(--badge-border)" }}>
            <Loader2 className="w-3 h-3 animate-spin" />
            {agentLabel} {t("chat.processing")}
          </div>
        )}
      </header>

      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center px-6">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4" style={{ background: "var(--bg-elevated)" }}>
              <Sparkles className="w-6 h-6" style={{ color: "var(--accent)" }} />
            </div>
            <h2 className="text-lg font-semibold mb-1.5" style={{ color: "var(--text-primary)" }}>{t("chat.howCanIHelp")}</h2>
            <p className="text-xs mb-6 text-center max-w-sm" style={{ color: "var(--text-muted)" }}>{t("chat.helpDesc")}</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-w-md w-full">
              {QUICK.map((q) => {
                const Icon = q.icon;
                return (
                  <button key={q.label} onClick={() => handleSend(q.question)}
                    className="group flex items-center gap-2 p-2.5 rounded-lg transition-all duration-150 text-left cursor-pointer"
                    style={{ border: "1px solid var(--border)" }}>
                    <Icon className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "var(--text-muted)" }} />
                    <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>{q.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="px-5 py-3 space-y-0.5">
            {messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)}
            {isProcessing && (
              <div className="flex items-start gap-2.5 py-1.5 animate-fade-in">
                <div className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0" style={{ background: "var(--bg-elevated)" }}>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: "var(--text-muted)" }} />
                </div>
                <div className="rounded-xl rounded-tl-sm px-3 py-2" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
                  <div className="flex items-center gap-1.5">
                    <div className="flex gap-0.5">
                      <span className="w-1 h-1 rounded-full typing-dot" style={{ background: "var(--text-muted)" }} />
                      <span className="w-1 h-1 rounded-full typing-dot" style={{ background: "var(--text-muted)" }} />
                      <span className="w-1 h-1 rounded-full typing-dot" style={{ background: "var(--text-muted)" }} />
                    </div>
                    <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                      {currentAgent === "supervisor" ? t("chat.coordinating") : agentLabel ? `${agentLabel} ${t("chat.processing")}` : t("chat.thinking")}
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="p-3 flex-shrink-0" style={{ background: "var(--bg-app)", borderTop: "1px solid var(--border-subtle)" }}>
        <div className="flex gap-2 items-center max-w-4xl mx-auto">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder={t("chat.typeMessage")}
            className="flex-1 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 transition-all"
            style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-primary)" }}
            disabled={isProcessing} />
          <button onClick={() => handleSend()} disabled={isProcessing || !input.trim()}
            className="p-2 rounded-lg text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer flex-shrink-0"
            style={{ background: "var(--accent)" }}>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
