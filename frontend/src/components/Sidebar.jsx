import React from "react";
import { Trash2, LogOut } from "lucide-react";

const Sidebar = ({ onLogout, onClear }) => {
  return (
    <div className="flex justify-between items-center px-6 py-2 bg-transparent text-white text-sm">
      <div
        onClick={onClear}
        className="flex items-center gap-1 cursor-pointer hover:text-purple-300 transition"
        title="Clear chat history"
      >
        <Trash2 size={14} strokeWidth={1.5} />
        <span>Clear Chat</span>
      </div>

      <div
        onClick={onLogout}
        className="flex items-center gap-1 cursor-pointer hover:text-purple-300 transition"
        title="Logout"
      >
        <LogOut size={14} strokeWidth={1.5} />
        <span>Logout</span>
      </div>
    </div>
  );
};

export default Sidebar;
