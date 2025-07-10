import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import Sidebar from "./Sidebar";
import { Paperclip, Send } from "lucide-react";

const ChatWindow = ({ user, setUser }) => {
  const [message, setMessage] = useState("");
  const [chats, setChats] = useState([]);
  const [file, setFile] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    axios.get(`/api/history/${user}`).then((res) => {
      setChats(res.data);
    });
  }, [user]);

  const handleSend = async () => {
    if (!message.trim()) return;
    const newChat = { username: user, message };
    setChats([...chats, newChat]);

    const res = await axios.post("/api/chat", {
      username: user,
      message,
    });
    setChats((prev) => [...prev, { username: "Agent", message: res.data.response }]);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    await axios.post("/api/upload", formData);
    alert("📁 File uploaded!");
    setFile(null);
  };

  const handleLogout = () => setUser(null);
  const handleClear = async () => {
    await axios.post("/api/clear_chat", { username: user });
    setChats([]);
  };

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chats]);

  return (
    <div className="flex flex-col h-screen">
      <Sidebar onLogout={handleLogout} onClear={handleClear} />

      <div className="flex-1 overflow-y-auto px-4 py-2 bg-black">
        {chats.map((chat, index) => (
          <div
            key={index}
            className={`flex ${chat.username === user ? "justify-end" : "justify-start"} mb-2`}
          >
            <div
              className={`px-4 py-2 rounded-xl max-w-xs ${
                chat.username === user ? "bg-blue-600" : "bg-gray-700"
              }`}
            >
              {chat.message}
            </div>
          </div>
        ))}
        <div ref={scrollRef}></div>
      </div>

      <div className="p-4 flex gap-2 items-center border-t border-gray-800 bg-gray-900">
        <label className="cursor-pointer">
          <Paperclip />
          <input
            type="file"
            className="hidden"
            onChange={(e) => setFile(e.target.files[0])}
          />
        </label>
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="flex-1 p-2 rounded bg-gray-800 text-white"
          placeholder="Type your message..."
        />
        <button
          onClick={handleSend}
          className="bg-blue-600 px-3 py-2 rounded hover:bg-blue-700"
        >
          <Send size={18} />
        </button>
        {file && (
          <button
            onClick={handleUpload}
            className="bg-green-600 px-2 py-1 rounded hover:bg-green-700 text-sm"
          >
            Upload
          </button>
        )}
      </div>
    </div>
  );
};

export default ChatWindow;
