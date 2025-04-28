async function sendMessage(event) {
    event.preventDefault();
    const input = document.querySelector("#message");
    const message = input.value.trim();
    if (message === "") return;
  
    addMessageToChat("user", message);
    input.value = "";
  
    // Yazıyor... mesajı ekle
    const chatBox = document.querySelector(".chat-box");
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "ai";
    loadingMsg.id = "loading-message";
    loadingMsg.innerHTML = "🤖 <br><em>Thinking...</em>";
    chatBox.appendChild(loadingMsg);
    chatBox.scrollTop = chatBox.scrollHeight;
  
    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: message })
      });
  
      const data = await response.json();
  
      // loading mesajını kaldır
      loadingMsg.remove();
  
      addMessageToChat("ai", data.response);
    } catch (error) {
      loadingMsg.innerHTML = "🤖 <br><em>Bir hata oluştu!</em>";
    }
  }
  
  


  function addMessageToChat(role, content) {
    const chatBox = document.querySelector(".chat-box");
    const msg = document.createElement("div");
    msg.className = role === "user" ? "user" : "ai";
  
    // Emojili, Markdown uyumlu içerik
    const emoji = role === "user" ? "🧍" : "🤖";
    msg.innerHTML = `${emoji} <br>${marked.parse(content).replace(/^<p>|<\/p>$/g, '')}`;
;
  
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
  
  
  
  async function resetChat() {
    await fetch("/reset");
    document.querySelector(".chat-box").innerHTML = "";
  }
  