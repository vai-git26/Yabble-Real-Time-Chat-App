# Real time Chat application 💬

A real-time chat application built with Django and WebSockets featuring group chats, private messaging, file sharing, voice messages, and person-to-person video calls

**Perfect for:**
- Community websites and forums
- Team collaboration platforms
- Social networking applications
- Educational platforms requiring group discussions
- Any web application needing integrated chat functionality

**Key Benefits:**
- No external chat service dependencies
- Full control over your data and privacy
- Customizable to match your brand and requirements
- Built with modern web technologies for optimal performance

## ✨ Features

- 🚀 Real-time messaging with WebSockets
- 👥 Public & private chat rooms
- 📁 File sharing (images, documents, audio)
- 📥 File download (images, voice messages, documents)
- 🎤 Voice message recording
- 📱 Push notifications
- 📹 Person-to-person video calling (private chats only)
- 👤 User profiles with avatars
- 🟢 Online status tracking
- 🔒 CAPTCHA protection for login
- ✉️ Email verification system

## 🛠️ Tech Stack

- **Backend**: Django 5.2.4, Django Channels, Daphne (ASGI server)
- **Database**: PostgreSQL
- **Real-time**: WebSockets, Django Channels (InMemoryChannelLayer)
- **Frontend**: HTMX, JavaScript, HTML5, CSS3
- **Authentication**: Django Allauth (email-based login)
- **File Storage**: Local file storage
- **Push Notifications**: Web Push API with VAPID keys
- **Video Calling**: WebRTC (RTCPeerConnection, getUserMedia), Custom WebSocket Signaling Server (CallConsumer), Google STUN Server (stun:stun.l.google.com:19302), ICE candidate negotiation, SDP offer/answer exchange
- **Voice Messages**: MediaRecorder API, getUserMedia for microphone access, WebM audio format, Real-time audio upload via AJAX, HTML5 audio player with download support
- **Security**: CAPTCHA protection, CSRF protection
- **Additional**: Pillow (image processing), WhiteNoise (static files)

## 🚀 Quick Start

1. **Clone & Setup**
   ```bash
   git clone <repo-url>
   cd real_chat
   python -m venv myenv
   myenv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   Create `.env` in `a_core/`:
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=True
   ENVIRONMENT=development
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   VAPID_PUBLIC_KEY=your-vapid-public-key
   VAPID_PRIVATE_KEY=your-vapid-private-key
   VAPID_ADMIN_EMAIL=admin@example.com
   ```

3. **Database & Run**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

## 📁 Project Structure

```
real_chat/
├── a_core/          # Django settings & config
├── a_users/         # User management
├── a_rtchat/        # Chat functionality
├── a_home/          # Home page
├── templates/       # HTML templates
├── static/          # CSS, JS, images
└── media/           # User uploaded files
```

## 🔧 Key Components

- **ChatGroup**: Manages chat rooms and members
- **GroupMessage**: Handles text, file, and voice messages with audio detection
- **WebSocket Consumers**: 
  - **ChatroomConsumer**: Real-time message broadcasting and online status
  - **CallConsumer**: WebRTC signaling for video calls (offer/answer/ICE candidates)
  - **OnlineStatusConsumer**: Global user presence tracking
- **Push Notifications**: Web Push API integration with VAPID authentication
- **Video Call System**: 
  - Frontend: WebRTC APIs (RTCPeerConnection, getUserMedia, MediaStream)
  - Backend: Django Channels AsyncWebsocketConsumer for signaling
  - STUN server integration for NAT traversal
- **Voice Message System**:
  - Frontend: MediaRecorder API for audio recording
  - Backend: File upload handling with audio format detection
  - Audio playback with HTML5 audio controls and download functionality

## 🌐 Main Endpoints

- `/` - Public chat
- `/chat/<room>/` - Specific chat room
- `/profile/` - User profile
- `/@<username>/` - View user profile

## 📱 Requirements

- Python 3.11+
- PostgreSQL
- Modern browser with WebSocket support

## 👨‍💻 Developer

This entire project was developed by **Vaibhav** - including all features, backend architecture, real-time messaging system, WebSocket implementation, user authentication, file sharing & downloading, voice messages, push notifications, CAPTCHA protection, email verification, and person-to-person video calling functionality.

## 📄 License

This project is open source.
