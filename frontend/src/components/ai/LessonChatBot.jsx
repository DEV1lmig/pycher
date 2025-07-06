import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Send, X } from "lucide-react";
import { streamChat } from "@/services/aiService";

const CHAT_STORAGE_KEY_PREFIX = "pycher_lesson_chat";

// Helper to save messages with a dynamic key
const saveMessages = (messages, key) => {
  try {
    // Only save if a unique key is provided
    if (key) {
      localStorage.setItem(key, JSON.stringify(messages));
    }
  } catch (error) {
    console.error("Failed to save chat messages:", error);
  }
};

// The component now requires userId and lessonId for unique chat history
export default function LessonChatBot({ onClose, lessonContext, starterCode, userId, lessonId }) {
  // Create a unique storage key for this specific user and lesson
  const uniqueChatKey = userId && lessonId ? `${CHAT_STORAGE_KEY_PREFIX}_${userId}_${lessonId}` : null;

  // Load messages from localStorage on initial render using the unique key
  const [messages, setMessages] = useState(() => {
    if (!uniqueChatKey) {
      return [{ from: "ai", text: "¡Hola! Soy tu tutor de Python. ¿En qué puedo ayudarte hoy?" }];
    }
    try {
      const savedMessages = localStorage.getItem(uniqueChatKey);
      return savedMessages ? JSON.parse(savedMessages) : [{ from: "ai", text: "¡Hola! Soy tu tutor de Python. ¿En qué puedo ayudarte hoy?" }];
    } catch (error) {
      console.error("Failed to load chat messages:", error);
      return [{ from: "ai", text: "¡Hola! Soy tu tutor de Python. ¿En qué puedo ayudarte hoy?" }];
    }
  });

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);


  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    setLoading(true);
    const userInput = input;
    setInput("");

    // 1. Add user message and save immediately
    const userMessage = { from: "user", text: userInput };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    saveMessages(updatedMessages, uniqueChatKey);

    // 2. Add a placeholder for the AI's response (without saving)
    const aiPlaceholder = { from: "ai", text: "" };
    setMessages(currentMsgs => [...currentMsgs, aiPlaceholder]);

    try {
      let fullAiResponse = "";
      // 3. Stream the AI response, updating only the UI state
      for await (const chunk of streamChat({
        code: userInput,
        lessonContext,
        starterCode
      })) {
        fullAiResponse += chunk;
        setMessages(currentMsgs => {
          const newMsgs = [...currentMsgs];
          newMsgs[newMsgs.length - 1].text = fullAiResponse;
          return newMsgs;
        });
      }

      // 4. Once streaming is complete, save the final state
      const finalMessages = [...updatedMessages, { from: "ai", text: fullAiResponse }];
      saveMessages(finalMessages, uniqueChatKey);

    } catch (err) {
      const errorText = "[Error de conexión. Inténtalo de nuevo.]";
      const finalMessages = [...updatedMessages, { from: "ai", text: errorText }];
      setMessages(finalMessages);
      saveMessages(finalMessages, uniqueChatKey);
    } finally {
      setLoading(false);
    }
  };

  return (
    // The main container is a flex column that fills the height of its parent (`h-full`).
    // `overflow-hidden` ensures the rounded corners are respected by child elements.
    <section className="flex flex-col h-full bg-[#1a1433] border border-[#312a56] rounded-lg shadow-lg overflow-hidden">
      {/* Header: `flex-shrink-0` prevents this from shrinking. */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 bg-[#312a56] border-b border-[#312a56]">
        <span className="font-bold text-white text-lg">Chat IA</span>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="text-white" />
        </Button>
      </div>

      {/* Messages Container: This is the key to the scrolling behavior.
          - `flex-1`: Makes this div take up all available vertical space.
          - `overflow-y-auto`: Adds a vertical scrollbar ONLY when messages overflow the div's height.
      */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex items-end gap-2 ${msg.from === 'ai' ? 'justify-start' : 'justify-end'}`}
          >
            <div
              className={`rounded-lg px-3 py-2 max-w-[85%] whitespace-pre-wrap text-sm shadow-md break-words
                ${msg.from === 'ai'
                  ? 'bg-[#23204a] text-gray-200'
                  : 'bg-[#5f2dee] text-white'
                }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form: `flex-shrink-0` prevents this from shrinking. */}
      <form
        className="flex-shrink-0 flex items-center gap-2 border-t border-[#312a56] p-4 bg-[#23204a]"
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
      >
        <input
          className="flex-1 border-none rounded-md px-3 py-2 bg-[#1a1433] text-white text-sm outline-none focus:ring-2 focus:ring-primary transition-shadow"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          placeholder={loading ? "Esperando respuesta..." : "Escribe tu pregunta..."}
        />
        <Button
          type="submit"
          disabled={loading || !input.trim()}
          size="icon"
          className="bg-primary hover:bg-primary-opaque text-white transition-colors disabled:bg-gray-500"
        >
          <Send size={18} />
        </Button>
      </form>
    </section>
  );
}
