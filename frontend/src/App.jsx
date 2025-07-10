import React, { useState } from "react";
import Login from "./components/Login";
import ChatWindow from "./components/ChatWindow";

function App() {
  const [user, setUser] = useState(null);
  return <>{user ? <ChatWindow user={user} setUser={setUser} /> : <Login setUser={setUser} />}</>;
}

export default App;
