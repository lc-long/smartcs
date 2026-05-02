import { useTranslation } from "react-i18next";
import type { ChatMessage } from "../../types";
import { User, Bot, AlertTriangle, CreditCard, Wrench, RotateCcw, MessageCircle, Headphones, GitBranch, WrenchIcon } from "lucide-react";

interface Props { message: ChatMessage; }

const agentConfig: Record<string, { nameKey: string; icon: typeof Bot; color: string; bg: string }> = {
  router: { nameKey: "agent.router", icon: GitBranch, color: "text-violet-400", bg: "bg-violet-950/50" },
  billing: { nameKey: "agent.billing", icon: CreditCard, color: "text-emerald-400", bg: "bg-emerald-950/50" },
  technical: { nameKey: "agent.techSupport", icon: Wrench, color: "text-sky-400", bg: "bg-sky-950/50" },
  refund: { nameKey: "agent.refund", icon: RotateCcw, color: "text-amber-400", bg: "bg-amber-950/50" },
  general: { nameKey: "agent.general", icon: MessageCircle, color: "text-zinc-400", bg: "bg-zinc-800/50" },
  escalation: { nameKey: "agent.human", icon: Headphones, color: "text-red-400", bg: "bg-red-950/50" },
  supervisor: { nameKey: "agent.router", icon: GitBranch, color: "text-zinc-500", bg: "bg-zinc-800/50" },
};

export default function MessageBubble({ message }: Props) {
  const { t } = useTranslation();
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center my-2 animate-fade-in">
        <div className="flex items-center gap-1.5 bg-amber-950/30 border border-amber-800/30 text-amber-400 text-[11px] px-3 py-1.5 rounded-full">
          <AlertTriangle className="w-3 h-3" />
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  const agent = message.agent_name ? agentConfig[message.agent_name] : null;
  const AgentIcon = agent?.icon || Bot;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} py-1 animate-slide-up`}>
      {!isUser && (
        <div className={`w-6 h-6 rounded flex items-center justify-center flex-shrink-0 mr-2 mt-0.5 ${agent?.bg || "bg-zinc-800"}`}>
          <AgentIcon className={`w-3.5 h-3.5 ${agent?.color || "text-zinc-500"}`} />
        </div>
      )}

      <div className="max-w-[75%]">
        {!isUser && agent && (
          <span className={`text-[10px] font-semibold ${agent.color} mb-0.5 block`}>{t(agent.nameKey)}</span>
        )}
        <div className={`${isUser ? "bg-indigo-600 text-white rounded-xl rounded-tr-sm" : "bg-zinc-900 border border-zinc-800 rounded-xl rounded-tl-sm"} px-3 py-2`}>
          <div className="text-[13px] whitespace-pre-wrap leading-relaxed">{formatContent(message.content, isUser)}</div>
          {message.tools_called.length > 0 && (
            <div className="mt-2 pt-1.5 border-t border-zinc-800 flex flex-wrap gap-1 items-center">
              <WrenchIcon className="w-3 h-3 text-zinc-500" />
              {message.tools_called.map((tool) => (
                <span key={tool} className="text-[10px] font-mono bg-zinc-800 text-zinc-400 px-1 py-0.5 rounded">{tool}</span>
              ))}
            </div>
          )}
          <div className={`text-[10px] mt-1.5 ${isUser ? "text-indigo-300" : "text-zinc-600"}`}>
            {new Date(message.created_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
          </div>
        </div>
      </div>

      {isUser && (
        <div className="w-6 h-6 rounded bg-indigo-900/50 flex items-center justify-center flex-shrink-0 ml-2 mt-0.5">
          <User className="w-3.5 h-3.5 text-indigo-400" />
        </div>
      )}
    </div>
  );
}

function formatContent(content: string, isUser: boolean): React.ReactNode {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let tableRows: string[] = [];
  let inTable = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith("|") && line.endsWith("|")) {
      if (!inTable) { inTable = true; tableRows = []; }
      tableRows.push(line);
    } else {
      if (inTable) { elements.push(renderTable(tableRows, elements.length, isUser)); tableRows = []; inTable = false; }
      if (line.startsWith("**") && line.endsWith("**")) {
        elements.push(<p key={i} className="font-semibold my-1">{line.slice(2, -2)}</p>);
      } else if (line.startsWith("- ") || line.startsWith("* ")) {
        elements.push(<li key={i} className="ml-3 my-0.5 list-disc text-[13px]">{line.slice(2)}</li>);
      } else if (/^\d+\./.test(line)) {
        elements.push(<li key={i} className="ml-3 my-0.5 list-decimal text-[13px]">{line.replace(/^\d+\.\s*/, "")}</li>);
      } else if (line) {
        elements.push(<p key={i} className="my-0.5">{line}</p>);
      }
    }
  }
  if (inTable && tableRows.length > 0) elements.push(renderTable(tableRows, elements.length, isUser));
  return <>{elements}</>;
}

function renderTable(rows: string[], key: number, isUser: boolean): React.ReactNode {
  if (rows.length < 2) return null;
  const headerCells = rows[0].split("|").slice(1, -1).map((c) => c.trim());
  const bodyRows = rows.slice(2).map((r) => r.split("|").slice(1, -1).map((c) => c.trim()));

  if (isUser) {
    return (
      <div key={key} className="overflow-x-auto my-1.5 text-[11px]">
        <table className="w-full border-collapse">
          <thead><tr className="border-b border-indigo-500/30">{headerCells.map((c, i) => <th key={i} className="px-1.5 py-0.5 text-left font-medium text-indigo-300">{c}</th>)}</tr></thead>
          <tbody>{bodyRows.map((r, i) => <tr key={i} className="border-b border-indigo-600/20">{r.map((c, j) => <td key={j} className="px-1.5 py-0.5 text-indigo-100">{c}</td>)}</tr>)}</tbody>
        </table>
      </div>
    );
  }

  return (
    <div key={key} className="overflow-x-auto my-1.5">
      <table className="w-full text-[12px] border-collapse">
        <thead><tr className="bg-zinc-800/50">{headerCells.map((c, i) => <th key={i} className="px-2 py-1 text-left text-[11px] font-semibold text-zinc-400 border-b border-zinc-800">{c}</th>)}</tr></thead>
        <tbody>{bodyRows.map((r, i) => <tr key={i} className="hover:bg-zinc-800/30 transition-colors">{r.map((c, j) => <td key={j} className="px-2 py-1 text-zinc-300 border-b border-zinc-800/50">{c}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}
