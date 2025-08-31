
self.addEventListener('push', function(event) {
  console.log('Push event received:', event);
  
  const data = event.data ? event.data.json() : {};
  console.log('Push data:', data);

  let title = data.title || 'New Message';
  let body = data.body || 'You have a new chat message';
  let icon = data.icon || '/static/images/ape1.jpg';

  // Special case: image/file notification (only if file_url exists)
  if (data.file_url && /\.(jpg|jpeg|png|gif|webp)$/i.test(data.file_url)) {
    title = data.title || '📷 New Image Message';
    body = 'Someone sent you an image!';
    icon = data.file_url; // show the actual image as icon
  }

  const options = {
    body: body,
    icon: icon,
    badge: '/static/images/ape1.jpg',
    data: { url: data.url || '/' },
    requireInteraction: false,
    silent: false
  };

  console.log('Showing notification with options:', options);

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const urlToOpen = event.notification.data && event.notification.data.url
    ? event.notification.data.url
    : '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
      for (const client of windowClients) {
        if (client.url.includes(urlToOpen) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});
