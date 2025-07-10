import React, { useState } from "react";

const Login = ({ setUser }) => {
  const [username, setUsername] = useState("");

  const handleLogin = () => {
    if (username.trim()) setUser(username);
  };

  return (
    <div className="h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-md w-96">
        <h2 className="text-white text-2xl mb-4">Login</h2>
        <input
          type="text"
          placeholder="Enter your name"
          className="w-full p-2 mb-4 rounded bg-gray-700 text-white"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <button
          onClick={handleLogin}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded"
        >
          Start Chat
        </button>
      </div>
    </div>
  );
};

export default Login;
