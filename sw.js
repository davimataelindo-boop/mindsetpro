self.addEventListener('install', event => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'REMINDER') {
    event.waitUntil(self.registration.showNotification('mindsetpro', {
      body: 'Seu treino de hoje está esperando por você.',
      icon: '/icon.svg',
      badge: '/icon.svg',
      tag: 'mente-forte-daily'
    }));
  }
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(clients.matchAll({type:'window', includeUncontrolled:true}).then(list => {
    if (list.length) return list[0].focus();
    return clients.openWindow('/');
  }));
});
