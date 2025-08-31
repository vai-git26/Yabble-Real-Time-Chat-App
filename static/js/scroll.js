function scrollToBottom() {
      const container = document.getElementById("chat_container");
      if (container) {
          container.scrollTop = container.scrollHeight;
      }
    }
// Initial scroll on load
scrollToBottom();



const chatContainer = document.getElementById("chat_container");
if (chatContainer) {
    const observer = new MutationObserver(() => {
        scrollToBottom();
    });
    observer.observe(chatContainer, { childList: true, subtree: true });
}

// Clear the message input when the server echoes the message back via ws
document.body.addEventListener('htmx:wsAfterSend', function() {
    const form = document.getElementById('chat_message_form');
    if (form) form.reset();
});
document.addEventListener("load", function(e) {
    if (e.target.tagName === "IMG") {
        scrollToBottom();
    }
}, true);
document.body.addEventListener("htmx:afterSettle", function () {
    scrollToBottom();
});