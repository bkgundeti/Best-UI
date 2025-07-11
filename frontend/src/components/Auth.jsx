import React, { useState } from "react";
import axios from "axios";
import { Eye, EyeOff } from "lucide-react";

const Auth = ({ setUser }) => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [mode, setMode] = useState("signup");
  const [error, setError] = useState("");

  const handleAuth = async () => {
    if (!username.trim() || !password.trim()) {
      setError("Username and password are required.");
      return;
    }

    try {
      const route = mode === "signup" ? "/signup" : "/login";
      const payload =
        mode === "signup"
          ? { username, email, password }
          : { username, password };

      const res = await axios.post(route, payload);

      if (res.data.success) {
        setUser(username);
      } else {
        setError(res.data.message || "Authentication failed.");
      }
    } catch (err) {
      const status = err.response?.status;
      const msg = err.response?.data?.message;

      if (status === 404) {
        setError("User does not exist.");
      } else if (status === 401) {
        setError("Incorrect password.");
      } else if (status === 409) {
        setError("Username or Email already exists.");
      } else {
        setError(msg || "Server error. Please try again.");
      }
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-gradient-to-br from-black via-gray-900 to-black">
      <div className="bg-gray-800 p-8 rounded-2xl shadow-xl w-full max-w-md">
        <h2 className="text-white text-3xl font-bold mb-6 text-center">
          {mode === "signup" ? "Create Your Account" : "Login to Your Account"}
        </h2>

        {error && (
          <div className="bg-red-500 text-white p-3 mb-4 rounded-lg text-sm">
            {error}
          </div>
        )}

        <input
          type="text"
          placeholder="Username"
          className="w-full p-3 mb-4 rounded-xl bg-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        {mode === "signup" && (
          <input
            type="email"
            placeholder="Email"
            className="w-full p-3 mb-4 rounded-xl bg-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        )}

        <div className="relative mb-4">
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Password"
            className="w-full p-3 pr-10 rounded-xl bg-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            type="button"
            className="absolute right-3 top-3 text-white"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
          </button>
        </div>

        <button
          onClick={handleAuth}
          className="w-full bg-purple-600 hover:bg-purple-700 transition-all duration-200 text-white py-3 rounded-full text-lg font-semibold shadow-md"
        >
          {mode === "signup" ? "Create Account" : "Login"}
        </button>

        <div className="mt-6 text-center text-gray-400 text-sm">
          {mode === "signup" ? (
            <>
              Already have an account?{" "}
              <button
                onClick={() => {
                  setMode("signin");
                  setError("");
                }}
                className="text-purple-400 underline hover:text-purple-300 transition"
              >
                Sign In
              </button>
            </>
          ) : (
            <>
              Don't have an account?{" "}
              <button
                onClick={() => {
                  setMode("signup");
                  setError("");
                }}
                className="text-purple-400 underline hover:text-purple-300 transition"
              >
                Sign Up
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Auth;
