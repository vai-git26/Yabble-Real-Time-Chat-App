document.addEventListener('DOMContentLoaded', function() {
    const wsElement = document.querySelector('[ws-connect]');
    if (wsElement) {
        wsElement.addEventListener('htmx:wsMessage', function(event) {
            let raw = event.detail.message;
            let data = null;

            try {
                data = typeof raw === "string" ? JSON.parse(raw) : raw;
            } catch (e) {
                data = null; // fallback if not JSON
            }

            if (data && data.type === "member_removed") {
                alert(data.message);
                window.location.href = data.redirect_url;
                return;
            }

            if (data && data.type === "chat_message") {
                alert(`New message from ${data.sender}: ${data.text}`);
                return;
            }

            console.log("Received normal chat:", raw);
        });
    }

    setInterval(function() {
        if (typeof groupName !== 'undefined' && groupName !== 'public-chat') {
            fetch(`/chat/check-membership/${groupName}`)
                .then(response => response.json())
                .then(data => {
                    if (!data.is_member) {
                        alert('You have been removed from this group.');
                        window.location.href = '/chat/room/public-chat';
                    }
                })
                .catch(error => console.log('Membership check failed:', error));
        }
    }, 5000);
});