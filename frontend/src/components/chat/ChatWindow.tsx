import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useChatStore } from "../../store/chatStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useAuth } from "../../contexts/AuthContext";
import type { WSEvent } from "../../types";
import MessageBubble from "./MessageBubble";
import { Send, Package, CreditCard, RotateCcw, Wrench, FileText, Phone, Sparkles, Loader2 } from "lucide-react";

const AGENT_LABELS: Record<string, string> = { billing: "billing", technical: "techSupport", refund: "refund", general: "general", escalation: "human", supervisor: "smartRouter" };
const AGENT_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  billing: { bg: "bg-emerald-950/50", text: "text-emerald-400", border: "border-emerald-800/50" },
  technical: { bg: "bg-sky-950/50", text: "text-sky-400", border: "border-sky-800/50" },
  refund: { bg: "bg-amber-950/50", text: "text-amber-400", border: "border-amber-800/50" },
  general: { bg: "bg-violet-950/50", text: "text-violet-400", border: "border-violet-800/50" },
  escalation: { bg: "bg-red-950/50", text: "text-red-400", border: "border-red-800/50" },
  supervisor: { bg: "bg-zinc-800/50", text: "text-zinc-400", border: "border-zinc-700/50" },
};

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

  const agentInfo = currentAgent ? { label: t(`agent.${AGENT_LABELS[currentAgent] || "general"}`), colors: AGENT_COLORS[currentAgent] || AGENT_COLORS.general } : null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="h-12 border-b border-zinc-800/50 px-5 flex items-center justify-between flex-shrink-0 bg-zinc-950">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h1 className="text-sm font-semibold text-zinc-100">{t("chat.title")}</h1>
          <div className="flex items-center gap-1 ml-2">
            <div className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-emerald-500" : "bg-amber-500 animate-pulse"}`} />
            <span className="text-[11px] text-zinc-500">{connected ? t("chat.connected") : t("chat.connecting")}</span>
          </div>
        </div>
        {isProcessing && agentInfo && (
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium border ${agentInfo.colors.bg} ${agentInfo.colors.text} ${agentInfo.colors.border}`}>
            <Loader2 className="w-3 h-3 animate-spin" />
            {agentInfo.label} {t("chat.processing")}
          </div>
        )}
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center px-6">
            <div className="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center mb-4">
              <Sparkles className="w-6 h-6 text-indigo-400" />
            </div>
            <h2 className="text-lg font-semibold text-zinc-100 mb-1.5">{t("chat.howCanIHelp")}</h2>
            <p className="text-xs text-zinc-500 mb-6 text-center max-w-sm">{t("chat.helpDesc")}</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-w-md w-full">
              {QUICK.map((q) => {
                const Icon = q.icon;
                return (
                  <button key={q.label} onClick={() => handleSend(q.question)}
                    className="group flex items-center gap-2 p-2.5 rounded-lg border border-zinc-800 hover:border-indigo-600/50 hover:bg-zinc-800/60 transition-all duration-150 text-left cursor-pointer">
                    <Icon className="w-3.5 h-3.5 text-zinc-500 group-hover:text-indigo-400 flex-shrink-0" />
                    <span className="text-xs font-medium text-zinc-400 group-hover:text-zinc-200">{q.label}</span>
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
                <div className="w-7 h-7 rounded-md bg-zinc-800 flex items-center justify-center flex-shrink-0">
                  <Loader2 className="w-3.5 h-3.5 text-zinc-500 animate-spin" />
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl rounded-tl-sm px-3 py-2">
                  <div className="flex items-center gap-1.5">
                    <div className="flex gap-0.5">
                      <span className="w-1 h-1 bg-zinc-500 rounded-full typing-dot" />
                      <span className="w-1 h-1 bg-zinc-500 rounded-full typing-dot" />
                      <span className="w-1 h-1 bg-zinc-500 rounded-full typing-dot" />
                    </div>
                    <span className="text-[11px] text-zinc-500">
                      {currentAgent === "supervisor" ? t("chat.coordinating") : agentInfo ? `${agentInfo.label} ${t("chat.processing")}` : t("chat.thinking")}
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-zinc-800/50 p-3 flex-shrink-0 bg-zinc-950">
        <div className="flex gap-2 items-center max-w-4xl mx-auto">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder={t("chat.typeMessage")}
            className="flex-1 border border-zinc-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600/50 transition-all placeholder:text-zinc-600 bg-zinc-900 text-zinc-100"
            disabled={isProcessing} />
          <button onClick={() => handleSend()} disabled={isProcessing || !input.trim()}
            className="p-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer flex-shrink-0">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
