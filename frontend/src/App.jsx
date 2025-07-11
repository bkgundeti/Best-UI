import React, { useState, useEffect } from "react";
import Auth from "./components/Auth";
import ChatWindow from "./components/ChatWindow";

function App() {
  const [user, setUser] = useState(null);

  // ✅ Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(storedUser);
    }
  }, []);

  // ✅ Save user to localStorage when set
  useEffect(() => {
    if (user) {
      localStorage.setItem("user", user);
    }
  }, [user]);

  return (
    <>
      {user ? (
        <ChatWindow user={user} setUser={setUser} />
      ) : (
        <Auth setUser={setUser} />
      )}
    </>
  );
}

export default App;
