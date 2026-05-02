import { useTranslation } from "react-i18next";
import type { ChatMessage } from "../../types";
import { User, Bot, AlertTriangle, CreditCard, Wrench, RotateCcw, MessageCircle, Headphones, GitBranch, WrenchIcon } from "lucide-react";

interface Props { message: ChatMessage; }

const agentConfig: Record<string, { nameKey: string; icon: typeof Bot; colorVar: string }> = {
  router: { nameKey: "agent.router", icon: GitBranch, colorVar: "--accent" },
  billing: { nameKey: "agent.billing", icon: CreditCard, colorVar: "--success" },
  technical: { nameKey: "agent.techSupport", icon: Wrench, colorVar: "--accent" },
  refund: { nameKey: "agent.refund", icon: RotateCcw, colorVar: "--warning" },
  general: { nameKey: "agent.general", icon: MessageCircle, colorVar: "--text-muted" },
  escalation: { nameKey: "agent.human", icon: Headphones, colorVar: "--error" },
  supervisor: { nameKey: "agent.router", icon: GitBranch, colorVar: "--text-dim" },
};

export default function MessageBubble({ message }: Props) {
  const { t } = useTranslation();
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center my-2 animate-fade-in">
        <div className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-full"
          style={{ background: "var(--badge-bg)", color: "var(--warning)", border: "1px solid var(--badge-border)" }}>
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
        <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 mr-2 mt-0.5"
          style={{ background: "var(--badge-bg)" }}>
          <AgentIcon className="w-3.5 h-3.5" style={{ color: agent ? `var(${agent.colorVar})` : "var(--text-muted)" }} />
        </div>
      )}

      <div className="max-w-[75%]">
        {!isUser && agent && (
          <span className="text-[10px] font-semibold mb-0.5 block" style={{ color: `var(${agent.colorVar})` }}>{t(agent.nameKey)}</span>
        )}
        <div className="px-3 py-2 rounded-xl"
          style={{
            background: isUser ? "var(--user-bubble)" : "var(--ai-bubble)",
            border: isUser ? "none" : "1px solid var(--ai-bubble-border)",
            color: isUser ? "var(--user-bubble-text)" : "var(--ai-bubble-text)",
            borderRadius: isUser ? "12px 12px 4px 12px" : "12px 12px 12px 4px",
          }}>
          <div className="text-[13px] whitespace-pre-wrap leading-relaxed">{formatContent(message.content)}</div>
          {message.tools_called.length > 0 && (
            <div className="mt-2 pt-1.5 flex flex-wrap gap-1 items-center" style={{ borderTop: "1px solid var(--border-subtle)" }}>
              <WrenchIcon className="w-3 h-3" style={{ color: "var(--text-muted)" }} />
              {message.tools_called.map((tool) => (
                <span key={tool} className="text-[10px] font-mono px-1 py-0.5 rounded"
                  style={{ background: "var(--badge-bg)", color: "var(--text-secondary)" }}>{tool}</span>
              ))}
            </div>
          )}
          <div className="text-[10px] mt-1.5" style={{ color: isUser ? "rgba(255,255,255,0.5)" : "var(--text-dim)" }}>
            {new Date(message.created_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
          </div>
        </div>
      </div>

      {isUser && (
        <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 ml-2 mt-0.5"
          style={{ background: "var(--badge-bg)" }}>
          <User className="w-3.5 h-3.5" style={{ color: "var(--accent)" }} />
        </div>
      )}
    </div>
  );
}

function formatContent(content: string): React.ReactNode {
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
      if (inTable) { elements.push(renderTable(tableRows, elements.length)); tableRows = []; inTable = false; }
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
  if (inTable && tableRows.length > 0) elements.push(renderTable(tableRows, elements.length));
  return <>{elements}</>;
}

function renderTable(rows: string[], key: number): React.ReactNode {
  if (rows.length < 2) return null;
  const headerCells = rows[0].split("|").slice(1, -1).map((c) => c.trim());
  const bodyRows = rows.slice(2).map((r) => r.split("|").slice(1, -1).map((c) => c.trim()));

  return (
    <div key={key} className="overflow-x-auto my-1.5">
      <table className="w-full text-[12px] border-collapse">
        <thead><tr style={{ background: "var(--badge-bg)" }}>
          {headerCells.map((c, i) => <th key={i} className="px-2 py-1 text-left text-[11px] font-semibold" style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>{c}</th>)}
        </tr></thead>
        <tbody>{bodyRows.map((r, i) => <tr key={i} className="transition-colors">
          {r.map((c, j) => <td key={j} className="px-2 py-1" style={{ color: "var(--text-secondary)", borderBottom: "1px solid var(--border-subtle)" }}>{c}</td>)}
        </tr>)}</tbody>
      </table>
    </div>
  );
}
