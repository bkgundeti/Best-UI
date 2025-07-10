import React from "react";

const Sidebar = ({ onLogout, onClear }) => {
  return (
    <div className="flex justify-between p-4 bg-gray-900 text-white text-sm border-b border-gray-700">
      <button onClick={onClear} className="hover:underline">Clear Chat</button>
      <button onClick={onLogout} className="hover:underline">Logout</button>
    </div>
  );
};

export default Sidebar;
