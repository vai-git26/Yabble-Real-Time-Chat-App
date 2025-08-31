const btnVideo = document.getElementById("btn-video");
const callPanel = document.getElementById("call-panel");
const localVideo = document.getElementById("localVideo");
const remoteVideo = document.getElementById("remoteVideo");
const btnAccept = document.getElementById("btn-accept");
const btnHang = document.getElementById("btn-hang");
const callStatus = document.getElementById("call-status");

// Exit early if video call elements don't exist on this page
if (!btnVideo || !callPanel) {
  console.log("Video call elements not found on this page");
} else {

let pc;
let localStream;
let incomingOffer = null;
let iceQueue = []; // store ICE candidates until remote description is set

// === Connect to Django CallConsumer WebSocket ===
const roomName = "testroom"; // both devices must use the SAME room name
const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
const socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/call/${roomName}/`);

socket.onmessage = async (event) => {
  const data = JSON.parse(event.data);
  console.log(" Received signal:", data);

  if (data.type === "offer") {
    callPanel.classList.remove("hidden");
    btnAccept.classList.remove("hidden");
    btnHang.classList.add("hidden");
    callStatus.innerText = "Incoming call...";
    incomingOffer = data;
  }

  else if (data.type === "answer") {
    await pc.setRemoteDescription({ type: "answer", sdp: data.sdp });
    callStatus.innerText = "Connected!";
    flushIceQueue();
  }

  else if (data.type === "ice-candidate") {
    if (pc && pc.remoteDescription && pc.remoteDescription.type) {
      try {
        await pc.addIceCandidate(data.candidate);
      } catch (err) {
        console.error("Error adding ICE candidate", err);
      }
    } else {
      console.log(" Queuing ICE candidate until remote description is set.");
      iceQueue.push(data.candidate);
    }
  }
};

// === Start call ===
btnVideo.addEventListener("click", async () => {
  callPanel.classList.remove("hidden");
  btnAccept.classList.add("hidden");
  btnHang.classList.remove("hidden");
  callStatus.innerText = "Starting call...";
  await startLocalVideo();
  createPeerConnection();
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  sendSignal({ type: "offer", sdp: offer.sdp });
  callStatus.innerText = "Offer sent. Waiting for answer...";
});

// === Accept call ===
btnAccept.addEventListener("click", async () => {
  btnAccept.classList.add("hidden");
  btnHang.classList.remove("hidden");
  callStatus.innerText = "Answering call...";
  await startLocalVideo();
  createPeerConnection();
  await pc.setRemoteDescription({ type: "offer", sdp: incomingOffer.sdp });
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  sendSignal({ type: "answer", sdp: answer.sdp });
  callStatus.innerText = "Answer sent. Connecting...";
  flushIceQueue();
});

// === Hang up ===
btnHang.addEventListener("click", () => {
  endCall();
});

async function startLocalVideo() {
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localVideo.srcObject = localStream;
    console.log(" Local video started");

    // If peer connection exists, add tracks
    if (pc) {
      localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
    }
  } catch (err) {
    alert("Could not access camera/mic: " + err);
  }
}

function createPeerConnection() {
  pc = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
  });

  if (localStream) {
    localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
  }

  pc.ontrack = event => {
    console.log(" Remote stream received");
    remoteVideo.srcObject = event.streams[0];
  };

  pc.onicecandidate = event => {
    if (event.candidate) {
      sendSignal({ type: "ice-candidate", candidate: event.candidate });
    }
  };
}

function sendSignal(message) {
  socket.send(JSON.stringify(message));
}

function flushIceQueue() {
  console.log(` Flushing ${iceQueue.length} queued ICE candidates`);
  iceQueue.forEach(async candidate => {
    try {
      await pc.addIceCandidate(candidate);
    } catch (err) {
      console.error("Error adding queued ICE candidate", err);
    }
  });
  iceQueue = [];
}



function endCall() {
  if (pc) {
    pc.close();
    pc = null;
  }

  //  Stop camera and mic
  if (localStream) {
    localStream.getTracks().forEach(track => track.stop());
    localStream = null;
  }

  // Clear video elements
  if (localVideo) localVideo.srcObject = null;
  if (remoteVideo) remoteVideo.srcObject = null;

  callPanel.classList.add("hidden");
  callStatus.innerText = "Call ended.";
}

} 