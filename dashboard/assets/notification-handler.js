// Notification Handler for AI Trading Assistant

class NotificationHandler {
  constructor() {
    this.isSubscribed = false;
    this.swRegistration = null;
    this.applicationServerPublicKey = null;
  }

  // Initialize the notification system
  async init(publicKey) {
    this.applicationServerPublicKey = publicKey || 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U';
    
    // Check if service workers and push messaging are supported
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.warn('Push notifications are not supported by this browser');
      return false;
    }

    try {
      // Register service worker
      this.swRegistration = await navigator.serviceWorker.register('/assets/service-worker.js');
      console.log('Service Worker registered successfully', this.swRegistration);
      
      // Check subscription status
      const subscription = await this.swRegistration.pushManager.getSubscription();
      this.isSubscribed = subscription !== null;
      
      return true;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      return false;
    }
  }

  // Convert base64 string to Uint8Array for the application server key
  urlB64ToUint8Array(base64String) {
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

  // Subscribe to push notifications
  async subscribe() {
    try {
      if (!this.swRegistration) {
        console.error('Service Worker not registered');
        return false;
      }

      const applicationServerKey = this.urlB64ToUint8Array(this.applicationServerPublicKey);
      const subscription = await this.swRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
      });

      console.log('User is subscribed to push notifications');
      this.isSubscribed = true;
      
      // Here you would typically send the subscription to your server
      // this.sendSubscriptionToServer(subscription);
      
      return subscription;
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
      return false;
    }
  }

  // Unsubscribe from push notifications
  async unsubscribe() {
    try {
      const subscription = await this.swRegistration.pushManager.getSubscription();
      
      if (!subscription) {
        console.log('No subscription to unsubscribe from');
        this.isSubscribed = false;
        return true;
      }

      await subscription.unsubscribe();
      console.log('User is unsubscribed from push notifications');
      this.isSubscribed = false;
      
      // Here you would typically inform your server about the unsubscription
      // this.removeSubscriptionFromServer(subscription);
      
      return true;
    } catch (error) {
      console.error('Failed to unsubscribe from push notifications:', error);
      return false;
    }
  }

  // Check if notifications are permitted
  async checkPermission() {
    if (!('Notification' in window)) {
      return 'unsupported';
    }
    
    return Notification.permission;
  }

  // Request notification permission
  async requestPermission() {
    if (!('Notification' in window)) {
      console.warn('Notifications not supported');
      return 'unsupported';
    }
    
    try {
      const permission = await Notification.requestPermission();
      return permission;
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return 'denied';
    }
  }

  // Display a test notification
  async showTestNotification() {
    if (this.isSubscribed && Notification.permission === 'granted') {
      const title = 'AI Trading Assistant';
      const options = {
        body: 'This is a test notification',
        icon: '/assets/icon-192x192.svg',
        badge: '/assets/icon-192x192.svg',
        vibrate: [100, 50, 100],
        data: {
          url: window.location.href
        },
        actions: [
          {
            action: 'view',
            title: 'View Dashboard'
          }
        ]
      };

      try {
        await this.swRegistration.showNotification(title, options);
        return true;
      } catch (error) {
        console.error('Error showing notification:', error);
        return false;
      }
    } else {
      console.warn('User is not subscribed to notifications or permission not granted');
      return false;
    }
  }
}

// Create global instance
const notificationHandler = new NotificationHandler();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = notificationHandler;
} else {
  window.notificationHandler = notificationHandler;
}