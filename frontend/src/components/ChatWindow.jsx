import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Paperclip, Send } from "lucide-react";

const ChatWindow = ({ user, setUser }) => {
  const [message, setMessage] = useState("");
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const scrollRef = useRef(null);
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;

    const storedUser = localStorage.getItem("user");
    if (!user && storedUser) {
      setUser(storedUser);
    }

    const fetchHistory = async () => {
      try {
        const res = await axios.get(`/history/${storedUser}`);
        setChats(res.data || []);
      } catch (err) {
        console.error("Error fetching chat history:", err);
      }
    };

    if (storedUser) {
      fetchHistory();
    }

    initialized.current = true;
  }, []);

  const handleSend = async () => {
    if (!message.trim() && !uploadedFile) return;

    const fileMsg = uploadedFile ? `📎 Uploaded: ${uploadedFile.name}` : null;
    const textMsg = message.trim();

    if (fileMsg) setChats((prev) => [...prev, { username: user, message: fileMsg }]);
    if (textMsg) setChats((prev) => [...prev, { username: user, message: textMsg }]);

    setMessage("");
    setUploadedFile(null);
    setLoading(true);

    // Show "Analyzing..." message
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

      const formattedResponse = res.data.response.trim();

      // Replace "Analyzing..." with final response
      setChats((prev) => {
        const updated = [...prev];
        const idx = updated.findIndex(
          (chat) => chat.username === "System" && chat.message === "Analyzing..."
        );
        if (idx !== -1) updated[idx] = { username: "Agent", message: formattedResponse };
        else updated.push({ username: "Agent", message: formattedResponse });
        return updated;
      });
    } catch (err) {
      console.error("Send failed:", err);
    }

    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
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

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chats, loading]);

  return (
    <div className="relative flex flex-col h-screen bg-gradient-to-br from-purple-950 via-black to-purple-900">
      {/* ✅ White Watermark (Visible) */}
      {chats.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center z-0 pointer-events-none">
          <h1 className="text-6xl font-bold text-white opacity-30 select-none">
            Model Selector AI Agent
          </h1>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center px-6 py-3 text-white text-sm border-b border-gray-700 z-10 bg-transparent">
        <span className="cursor-pointer hover:underline" onClick={handleClear}>
          Clear Chat
        </span>
        <span className="cursor-pointer hover:underline" onClick={handleLogout}>
          Logout
        </span>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 text-white relative z-10">
        <div className="relative z-10">
          {chats.map((chat, index) => {
            const isUser = chat.username === user;
            const isAgent = chat.username === "Agent";
            const isSystem = chat.username === "System";

            return (
              <div
                key={index}
                className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}
              >
                <div
                  className={`max-w-[85%] px-4 py-2 whitespace-pre-wrap ${
                    isUser
                      ? "bg-purple-600 rounded-xl rounded-br-sm"
                      : isAgent
                      ? "bg-gray-700 rounded-xl rounded-bl-sm"
                      : "text-sm italic text-gray-400"
                  }`}
                >
                  {chat.message}
                </div>
              </div>
            );
          })}
          <div ref={scrollRef}></div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-3 bg-gray-900 border-t border-gray-700 z-10">
        {uploadedFile && (
          <div className="text-sm text-green-400 mb-2">
            📁 Selected: {uploadedFile.name}
          </div>
        )}

        <div className="flex gap-2 items-end">
          <label className="cursor-pointer text-white">
            <Paperclip />
            <input
              type="file"
              className="hidden"
              onChange={(e) => handleUpload(e.target.files[0])}
            />
          </label>

          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your message..."
            rows={Math.min(5, message.split("\n").length)}
            className="flex-1 px-3 py-2 rounded-xl bg-gray-800 text-white resize-none overflow-hidden max-h-[200px] focus:outline-none"
          />

          <button
            onClick={handleSend}
            className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-xl text-white transition"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
