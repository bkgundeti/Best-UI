import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Paperclip, Send } from "lucide-react";

const ChatWindow = ({ user, setUser }) => {
  const [message, setMessage] = useState("");
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const scrollRef = useRef(null);
  const textareaRef = useRef(null);
  const initialized = useRef(false);
  const isMobile = /Mobi|Android/i.test(navigator.userAgent);

  useEffect(() => {
    if (initialized.current) return;
    const storedUser = localStorage.getItem("user");
    if (!user && storedUser) setUser(storedUser);

    const fetchHistory = async () => {
      try {
        const res = await axios.get(`/history/${storedUser}`);
        setChats(res.data || []);
      } catch (err) {
        console.error("Error fetching chat history:", err);
      }
    };

    if (storedUser) fetchHistory();
    initialized.current = true;
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chats]);

  const resetTextareaHeight = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
    }
  };

  const handleSend = async () => {
    if (!message.trim() && !uploadedFile) return;

    const fileMsg = uploadedFile ? `📎 Uploaded: ${uploadedFile.name}` : null;
    const textMsg = message.trim();

    if (fileMsg) setChats((prev) => [...prev, { username: user, message: fileMsg }]);
    if (textMsg) setChats((prev) => [...prev, { username: user, message: textMsg }]);

    setMessage("");
    setUploadedFile(null);
    resetTextareaHeight();
    setLoading(true);

    setChats((prev) => [...prev, { username: "System", message: "Analyzing..." }]);

    try {
      if (uploadedFile) {
        const formData = new FormData();
        formData.append("file", uploadedFile);
        await axios.post("/upload", formData);
      }

      const res = await axios.post("/chat", {
        username: user,
        message: textMsg || fileMsg,
      });

      const formattedResponse = res.data?.response?.trim() || "⚠️ No proper response received.";

      setChats((prev) => {
        const updated = [...prev];
        const index = updated.findIndex(
          (chat) => chat.username === "System" && chat.message === "Analyzing..."
        );
        if (index !== -1) {
          updated[index] = { username: "Agent", message: formattedResponse };
        } else {
          updated.push({ username: "Agent", message: formattedResponse });
        }
        return updated;
      });
    } catch (err) {
      console.error("Send failed:", err);
      setChats((prev) => [
        ...prev,
        { username: "Agent", message: "⚠️ Something went wrong." },
      ]);
    }

    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (!isMobile && e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleUpload = (file) => {
    if (file) setUploadedFile(file);
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    setUser(null);
    setChats([]);
  };

  const handleClear = async () => {
    try {
      await axios.post("/clear_chat", { username: user });
      setChats([]);
    } catch (err) {
      console.error("Clear failed:", err);
    }
  };

  const handleTextareaInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 150) + "px";
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-[#0f0f0f] via-[#1a0033] to-[#2a0055] text-white overflow-hidden relative">

      {/* Light Watermark */}
      {chats.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
          <h1 className="text-5xl font-bold text-white/30 text-center">
            Model Selector AI Agent
          </h1>
        </div>
      )}

      {/* Sticky Header */}
      <div className="sticky top-0 z-20 flex justify-between items-center px-4 py-2 text-sm border-b border-gray-700 bg-gray-950">
        <button onClick={handleClear} className="hover:underline">Clear Chat</button>
        <button onClick={handleLogout} className="hover:underline">Logout</button>
      </div>

      {/* Chat Window */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-3">
        {chats.map((chat, index) => {
          const isUser = chat.username === user;
          const isAgent = chat.username === "Agent";
          const isSystem = chat.username === "System";

          return (
            <div key={index} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] px-4 py-2 rounded-xl text-sm shadow-md whitespace-pre-wrap break-words ${
                  isUser
                    ? "bg-purple-600 text-white rounded-br-sm"
                    : isAgent
                    ? "bg-gray-800 text-white rounded-bl-sm"
                    : "text-gray-400 italic"
                }`}
              >
                {chat.message}
              </div>
            </div>
          );
        })}
        <div ref={scrollRef} />
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-700 bg-gray-900">
        {uploadedFile && (
          <div className="text-sm text-green-400 mb-1">
            📁 Selected: {uploadedFile.name}
          </div>
        )}
        <div className="flex gap-2 items-end">
          <label className="cursor-pointer">
            <Paperclip />
            <input
              type="file"
              className="hidden"
              onChange={(e) => handleUpload(e.target.files[0])}
              disabled={loading}
            />
          </label>

          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => {
              setMessage(e.target.value);
              handleTextareaInput();
            }}
            onKeyDown={handleKeyPress}
            placeholder={loading ? "Analyzing..." : "Type your message..."}
            rows={1}
            className="flex-1 px-3 py-2 rounded-xl bg-gray-800 text-white resize-none overflow-auto max-h-[150px] focus:outline-none"
            disabled={loading}
          />

          <button
            onClick={handleSend}
            disabled={loading || (!message.trim() && !uploadedFile)}
            className={`px-3 py-2 rounded-xl text-white transition ${
              loading ? "bg-gray-500" : "bg-purple-600 hover:bg-purple-700"
            }`}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
