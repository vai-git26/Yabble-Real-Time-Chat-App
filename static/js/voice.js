let mediaRecorder;
let audioChunks = [];

const recordBtn = document.getElementById("record-btn");
const stopBtn = document.getElementById("stop-btn");
const voiceControls = document.querySelector(".voice-controls");
const recordStatus = document.getElementById("record-status");

recordBtn.addEventListener("click", async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        audioChunks = [];
        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
            const formData = new FormData();
            formData.append("audio", audioBlob, "voice_message.webm");

            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            try {
                const response = await fetch(`/chat/audio-upload/${groupName}/`, {
                    method: "POST",
                    headers: { "X-CSRFToken": csrftoken },
                    body: formData,
                    credentials: "same-origin"
                });

                if (!response.ok) {
                    console.error("Upload failed:", await response.text());
                } else {
                    console.log("Audio uploaded successfully");
                }
            } catch (error) {
                console.error("Error uploading audio:", error);
            }
        };

        mediaRecorder.start();
        console.log("Recording started");
        voiceControls.style.display = "flex";
        recordStatus.textContent = "Recording...";
    } catch (err) {
        console.error("Microphone access denied", err);
    }
});

stopBtn.addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        console.log("Recording stopped");
    }
    voiceControls.style.display = "none";
});
