function toggleChat() {
    const chatBox = document.getElementById('chatBox');
    chatBox.style.display = chatBox.style.display === 'flex' ? 'none' : 'flex';
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const msgContainer = document.getElementById('chatMessages');
    if (!input.value) return;

    // Append User Message
    msgContainer.innerHTML += `<div class="user-msg">${input.value}</div>`;
    
    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input.value })
    });
    const data = await response.json();

    // Append Bot Message
    msgContainer.innerHTML += `<div class="bot-msg">${data.reply}</div>`;
    input.value = '';
    msgContainer.scrollTop = msgContainer.scrollHeight;
}
function toggleChat() {
    const window = document.getElementById('chat-window');
    window.style.display = (window.style.display === 'none' || window.style.display === '') ? 'flex' : 'none';
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const container = document.getElementById('chat-messages');
    const text = input.value.trim();

    if (!text) return;

    // Add User Message
    container.innerHTML += `<div class="msg user">${text}</div>`;
    input.value = '';
    container.scrollTop = container.scrollHeight;

    // Call Flask API
    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
    });
    
    const data = await response.json();

    // Add Bot Message
    setTimeout(() => {
        container.innerHTML += `<div class="msg bot">${data.reply}</div>`;
        container.scrollTop = container.scrollHeight;
    }, 500);
}