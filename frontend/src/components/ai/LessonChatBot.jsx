import { useState, useRef } from "react";
import { Button } from "../ui/button";
import { ChevronUp, ChevronDown, Send } from "lucide-react";
import { streamChat } from "@/services/aiService";

export default function LessonChatbot() {
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState([
    { from: "ai", text: "¡Hola! Soy tu tutor de Python. ¿En qué puedo ayudarte hoy?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingMsg, setStreamingMsg] = useState("");
  const abortRef = useRef(null);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setMessages(msgs => [...msgs, { from: "user", text: input }]);
    setStreamingMsg("");
    let aiMsg = { from: "ai", text: "" };
    setMessages(msgs => [...msgs, aiMsg]);
    const aiMsgIndex = messages.length + 1;

    try {
      let text = "";
      for await (const chunk of streamChat({ code: input })) {
        text += chunk;
        setStreamingMsg(text);
        setMessages(msgs => {
          const newMsgs = [...msgs];
          newMsgs[aiMsgIndex] = { ...aiMsg, text };
          return newMsgs;
        });
      }
    } catch (err) {
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
    <div className={`fixed bottom-4 right-4 z-50 transition-all duration-300 ${expanded ? "w-96 h-[32rem]" : "w-64 h-14"}`}>
      <div className="bg-[#1a1433] border border-[#312a56] rounded-lg shadow-lg flex flex-col h-full">
        <div
          className="flex items-center justify-between px-4 py-2 cursor-pointer bg-[#312a56] rounded-t-lg"
          onClick={() => setExpanded(e => !e)}
        >
          <span className="font-bold text-white">Chat IA</span>
          {expanded ? <ChevronDown className="text-white" /> : <ChevronUp className="text-white" />}
        </div>
        {expanded && (
          <>
            <div className="flex-1 p-3 overflow-y-auto bg-[#1a1433]">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`mb-2 ${msg.from === "ai"
                    ? "text-blue-200 bg-[#23204a] rounded-lg p-2 max-w-[90%]"
                    : "text-gray-200 bg-[#312a56] rounded-lg p-2 ml-auto max-w-[90%] text-right"
                  }`}
                >
                  <span className="block whitespace-pre-wrap">{msg.text}</span>
                </div>
              ))}
              {loading && (
                <div className="text-blue-300 bg-[#23204a] rounded-lg p-2 max-w-[90%]">
                  <span className="block whitespace-pre-wrap">{streamingMsg || "..."}</span>
                </div>
              )}
            </div>
            <div className="flex border-t border-[#312a56] p-2 bg-[#23204a]">
              <input
                className="flex-1 border rounded px-2 py-1 mr-2 bg-[#1a1433] text-white"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !loading && sendMessage()}
                disabled={loading}
                placeholder="Escribe tu pregunta..."
              />
              <Button onClick={sendMessage} disabled={loading || !input.trim()} size="sm" className="bg-[#5f2dee] hover:bg-[#4f25c5] text-white">
                <Send size={16} />
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
