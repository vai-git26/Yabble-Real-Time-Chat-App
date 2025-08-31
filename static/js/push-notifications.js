// Push Notification Handler
class PushNotificationManager {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.vapidPublicKey = null;
        this.subscription = null;
    }

    async init(vapidPublicKey) {
        if (!this.isSupported) {
            console.log('Push notifications not supported');
            return;
        }

        this.vapidPublicKey = vapidPublicKey;
        
        // Check notification permission
        if (Notification.permission === 'denied') {
            console.log('Notification permission denied');
            return;
        }
        
        // Request permission if not granted
        if (Notification.permission !== 'granted') {
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                console.log('Notification permission not granted');
                return;
            }
        }
        
        // Register service worker
        try {
            const registration = await navigator.serviceWorker.register('/service-worker.js');
            console.log('Service Worker registered:', registration);
            
            // Wait for service worker to be ready
            await navigator.serviceWorker.ready;
            
            // Check for existing subscription
            this.subscription = await registration.pushManager.getSubscription();
            if (!this.subscription) {
                console.log('No existing push subscription found, creating new one...');
                await this.subscribeToPush();
            } else {
                console.log('Existing subscription found');
                await this.saveSubscription(this.subscription);
            }
        } catch (error) {
            console.error('Service Worker registration failed:', error);
        }
    }

    async subscribeToPush() {
        if (!this.vapidPublicKey) {
            console.error('VAPID public key not provided');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            this.subscription = subscription;
            await this.saveSubscription(subscription);
            console.log('Push subscription successful');
        } catch (error) {
            console.error('Push subscription failed:', error);
        }
    }




    
    async saveSubscription(subscription) {
        const subscriptionData = {
            endpoint: subscription.endpoint,
            keys: {
                p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh')))),
                auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth'))))
            }
        };

        try {
            const response = await fetch('/chat/save-push-subscription/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(subscriptionData)
            });

            if (response.ok) {
                console.log('Subscription saved to server');
            } else {
                console.error('Failed to save subscription');
            }
        } catch (error) {
            console.error('Error saving subscription:', error);
        }
    }

    // Status updates removed for cleaner UI

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    // Test notification method removed - notifications are now handled automatically
}

// Initialize push notifications when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing push notifications...');
    
    const pushManager = new PushNotificationManager();
    
    // Get VAPID public key from meta tag or template
    const vapidKeyMeta = document.querySelector('meta[name="vapid-public-key"]');
    if (vapidKeyMeta) {
        const vapidPublicKey = vapidKeyMeta.content;
        console.log('Found VAPID public key:', vapidPublicKey.substring(0, 20) + '...');
        pushManager.init(vapidPublicKey);
    } else {
        console.error('VAPID public key not found in meta tag');
    }
    
    // Make it globally available for testing
    window.pushManager = pushManager;
});
