import React, { useState } from "react";

interface MessageBubbleProps {
  message: string;
  sender: "user" | "ai";
  timestamp: Date;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, sender, timestamp }) => {
  const [showCopy, setShowCopy] = useState(false);
  const [copied, setCopied] = useState(false);
  const isUser = sender === "user";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const ta = document.createElement("textarea");
      ta.value = message;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const renderContent = (text: string) => {
    const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(renderInlineText(text.slice(lastIndex, match.index), `pre-${match.index}`));
      }
      parts.push(
        <pre
          key={`code-${match.index}`}
          className="bg-gray-950 text-green-400 rounded-md p-3 my-2 overflow-x-auto text-xs font-mono"
        >
          {match[1] && (
            <div className="text-gray-500 text-[10px] mb-1 uppercase">{match[1]}</div>
          )}
          <code>{match[2].trim()}</code>
        </pre>
      );
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
      parts.push(renderInlineText(text.slice(lastIndex), `post-${lastIndex}`));
    }

    return parts.length > 0 ? parts : renderInlineText(text, "full");
  };

  const renderInlineText = (text: string, key: string) => {
    const inlineCode = text.replace(/`([^`]+)`/g, '<code class="bg-gray-700 px-1 rounded text-xs font-mono text-yellow-300">$1</code>');
    const bolded = inlineCode.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    return (
      <span key={key} dangerouslySetInnerHTML={{ __html: bolded }} className="whitespace-pre-wrap" />
    );
  };

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      onMouseEnter={() => setShowCopy(true)}
      onMouseLeave={() => setShowCopy(false)}
    >
      <div className={`relative max-w-[75%] group`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-blue-600 text-white rounded-br-sm"
              : "bg-gray-700 text-gray-100 rounded-bl-sm"
          }`}
        >
          {renderContent(message)}
        </div>

        <div className={`flex items-center gap-2 mt-1 ${isUser ? "justify-end" : "justify-start"}`}>
          <span className="text-[10px] text-gray-500">{formatTime(timestamp)}</span>
          {showCopy && (
            <button
              onClick={handleCopy}
              className="text-[10px] text-gray-500 hover:text-white transition"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
