import React, { useState, useRef } from "react";
import { ChatMessageList } from "@/components/ui/chat/chat-message-list";
import { ChatInput } from "@/components/ui/chat/chat-input";
import { ChatBubble, ChatBubbleMessage, ChatBubbleAvatar } from "@/components/ui/chat/chat-bubble";
import { Button } from "@/components/ui/button";
import { X, Send } from "lucide-react";
import { streamChat } from "@/services/aiService";
import { useAutoScroll } from "@/components/ui/chat/hooks/useAutoScroll";

export default function LessonChatDrawer({
  lessonContent,
  exercisePrompt,
  open: controlledOpen,
  onOpenChange,
}) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen;
  const setOpen = onOpenChange || setInternalOpen;
  const [messages, setMessages] = useState([
    {
      from: "ai",
      text: "¡Hola! Soy tu tutor de Python. ¿En qué puedo ayudarte hoy?"
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingMsg, setStreamingMsg] = useState("");
  const inputRef = useRef();

  // Auto-scroll
  const {
    scrollRef,
    disableAutoScroll,
  } = useAutoScroll({
    content: messages,
    smooth: true,
  });

  // Avatars (replace with your own images if desired)
  const aiAvatar = "https://api.dicebear.com/7.x/bottts/svg?seed=ai";
  const userAvatar = "https://api.dicebear.com/7.x/personas/svg?seed=user";

  // Send message and stream AI response
  const sendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;
    setLoading(true);
    setMessages(msgs => [...msgs, { from: "user", text: input }]);
    setStreamingMsg("");
    let aiMsg = { from: "ai", text: "" };
    setMessages(msgs => [...msgs, aiMsg]);
    const aiMsgIndex = messages.length + 1;
    try {
      let text = "";
      for await (const chunk of streamChat({
        code: input,
        instruction: exercisePrompt || lessonContent || ""
      })) {
        text += chunk;
        setStreamingMsg(text);
        setMessages(msgs => {
          const newMsgs = [...msgs];
          newMsgs[aiMsgIndex] = { ...aiMsg, text };
          return newMsgs;
        });
      }
    } catch {
      setStreamingMsg("[Error de conexión]");
      setMessages(msgs => {
        const newMsgs = [...msgs];
        newMsgs[aiMsgIndex] = { ...aiMsg, text: "[Error de conexión]" };
        return newMsgs;
      });
    }
    setLoading(false);
    setInput("");
    setStreamingMsg("");
  };

  return (
    <div
      className={`fixed top-0 right-0 h-full z-[9999] bg-dark rounded-l-3xl border-l-4 border-primary-opaque shadow-2xl transition-transform duration-300
        ${open ? "translate-x-0" : "translate-x-full"}
        flex flex-col w-full max-w-[400px]`}
      style={{ minWidth: 320, backgroundColor: "#160f30" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-primary-opaque bg-[#1a1433] rounded-tl-3xl">
        <span className="font-bold text-primary text-lg">Chat IA</span>
        <button
          className="text-primary hover:text-secondary bg-[#232232] rounded-full p-2 transition"
          onClick={() => setOpen(false)}
          aria-label="Cerrar chat"
        >
          <X size={22} />
        </button>
      </div>
      {/* Chat body with scroll */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <ChatMessageList
          className="flex-1 min-h-0 overflow-y-auto px-4 py-4 custom-scroll"
          ref={scrollRef}
          onWheel={disableAutoScroll}
          onTouchMove={disableAutoScroll}
        >
          {messages.map((msg, idx) => (
            <ChatBubble
              key={idx}
              variant={msg.from === "user" ? "sent" : "received"}
              layout="default"
              className={
                (msg.from === "user"
                  ? "justify-end"
                  : "justify-start") +
                " rounded-2xl mb-3"
              }
            >
              <ChatBubbleAvatar
                src={msg.from === "user" ? userAvatar : aiAvatar}
                fallback={msg.from === "user" ? "U" : "AI"}
                className={
                  msg.from === "user"
                    ? "order-2 ml-3 ring-2 ring-primary"
                    : "order-1 mr-3 ring-2 ring-secondary"
                }
              />
              <ChatBubbleMessage
                className={
                  msg.from === "user"
                    ? "bg-primary text-white rounded-2xl rounded-br-sm"
                    : "bg-[#232232] text-secondary rounded-2xl rounded-bl-sm"
                }
              >
                {msg.text}
              </ChatBubbleMessage>
            </ChatBubble>
          ))}
          {loading && (
            <ChatBubble variant="received" layout="default" className="rounded-2xl mb-3">
              <ChatBubbleAvatar src={aiAvatar} fallback="AI" className="mr-3 ring-2 ring-secondary" />
              <ChatBubbleMessage isLoading className="bg-[#232232] text-secondary rounded-2xl rounded-bl-sm">
                {streamingMsg ? streamingMsg : "..."}
              </ChatBubbleMessage>
            </ChatBubble>
          )}
        </ChatMessageList>
      </div>
      {/* Chat input */}
      <form
        className="p-4 border-t border-primary-opaque bg-[#1a1433] rounded-b-3xl flex gap-2"
        onSubmit={sendMessage}
      >
        <ChatInput
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={loading}
          placeholder="Escribe tu mensaje..."
          className="rounded-2xl bg-[#232232] text-white border-none focus:ring-2 focus:ring-primary"
        />
        <Button
          type="submit"
          size="icon"
          className="ml-2 bg-primary hover:bg-primary-light text-white rounded-full"
          disabled={loading || !input.trim()}
        >
          <Send size={20} />
        </Button>
      </form>
    </div>
  );
}
