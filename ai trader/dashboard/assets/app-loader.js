// App Loader for AI Trading Assistant
// Handles performance optimization and offline functionality

// Performance optimization - lazy loading and code splitting
class AppLoader {
  constructor() {
    this.resources = {
      loaded: false,
      charts: false,
      data: false
    };
    this.offlineMode = false;
  }

  // Initialize the app loader
  init() {
    // Check if we're online
    this.updateOnlineStatus();
    
    // Listen for online/offline events
    window.addEventListener('online', () => this.updateOnlineStatus());
    window.addEventListener('offline', () => this.updateOnlineStatus());
    
    // Optimize resource loading
    this.optimizeResourceLoading();
    
    // Register performance monitoring
    this.monitorPerformance();
  }

  // Update online status and handle offline mode
  updateOnlineStatus() {
    const isOnline = navigator.onLine;
    this.offlineMode = !isOnline;
    
    // Update UI based on connection status
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
      if (isOnline) {
        statusElement.textContent = 'Online';
        statusElement.className = 'status-indicator online';
      } else {
        statusElement.textContent = 'Offline';
        statusElement.className = 'status-indicator offline';
        
        // Show offline notification
        this.showOfflineNotification();
      }
    }
    
    // If we're offline, load cached data
    if (this.offlineMode) {
      this.loadCachedData();
    }
  }

  // Show notification when app goes offline
  showOfflineNotification() {
    // Create notification if it doesn't exist
    let notification = document.getElementById('offline-notification');
    if (!notification) {
      notification = document.createElement('div');
      notification.id = 'offline-notification';
      notification.className = 'offline-notification';
      notification.innerHTML = `
        <div class="notification-content">
          <span>You are currently offline. Some features may be limited.</span>
          <button class="close-notification" aria-label="Close notification">×</button>
        </div>
      `;
      document.body.appendChild(notification);
      
      // Add event listener to close button
      notification.querySelector('.close-notification').addEventListener('click', () => {
        notification.classList.add('hidden');
      });
    }
    
    // Show the notification
    notification.classList.remove('hidden');
  }

  // Load cached data when offline
  loadCachedData() {
    // Check if we have cached data in localStorage
    const cachedPortfolioData = localStorage.getItem('portfolio-data');
    const cachedTradesData = localStorage.getItem('trades-data');
    const cachedAlertsData = localStorage.getItem('alerts-data');
    
    if (cachedPortfolioData) {
      try {
        // Update the data stores with cached data
        const portfolioStore = document.getElementById('portfolio-data-store');
        if (portfolioStore) {
          portfolioStore.textContent = cachedPortfolioData;
          // Trigger a custom event to notify that data is available
          const event = new CustomEvent('data-loaded');
          portfolioStore.dispatchEvent(event);
        }
      } catch (error) {
        console.error('Error loading cached portfolio data:', error);
      }
    }
    
    // Similar for trades and alerts data
    // ...
  }

  // Optimize resource loading
  optimizeResourceLoading() {
    // Use Intersection Observer to lazy load charts
    if ('IntersectionObserver' in window) {
      const chartObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const chartContainer = entry.target;
            const chartId = chartContainer.querySelector('.js-plotly-plot')?.id;
            
            if (chartId) {
              // Trigger chart render when visible
              const event = new CustomEvent('render-chart', { detail: { chartId } });
              document.dispatchEvent(event);
            }
            
            // Unobserve after loading
            observer.unobserve(chartContainer);
          }
        });
      }, { threshold: 0.1 });
      
      // Observe all chart containers
      document.querySelectorAll('.chart-container').forEach(container => {
        chartObserver.observe(container);
      });
    }
    
    // Preconnect to data sources
    this.addPreconnect('https://query1.finance.yahoo.com');
  }

  // Add preconnect hint for performance
  addPreconnect(url) {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = url;
    document.head.appendChild(link);
  }

  // Monitor performance metrics
  monitorPerformance() {
    if ('performance' in window && 'PerformanceObserver' in window) {
      // Create performance observer for Largest Contentful Paint
      const lcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        const lastEntry = entries[entries.length - 1];
        console.log('LCP:', lastEntry.startTime);
        
        // Report to analytics or adjust app behavior based on performance
        if (lastEntry.startTime > 2500) {
          // Slow loading - consider reducing chart complexity
          this.optimizeCharts();
        }
      });
      
      // Start observing LCP
      lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
    }
  }

  // Optimize charts for better performance
  optimizeCharts() {
    // Reduce chart complexity for better performance
    document.querySelectorAll('.js-plotly-plot').forEach(chart => {
      // Send message to Plotly to use simpler rendering
      if (window.Plotly) {
        try {
          const chartId = chart.id;
          if (chartId) {
            // Reduce point density and animation complexity
            const update = {
              'line.simplify': true,
              'line.shape': 'linear'
            };
            window.Plotly.restyle(chartId, update);
          }
        } catch (e) {
          console.error('Error optimizing chart:', e);
        }
      }
    });
  }

  // Cache data for offline use
  cacheData(key, data) {
    try {
      localStorage.setItem(key, data);
    } catch (e) {
      console.error('Error caching data:', e);
      // If localStorage is full, clear old items
      if (e.code === 22 || e.code === 1014) {
        this.clearOldCache();
        try {
          localStorage.setItem(key, data);
        } catch (e2) {
          console.error('Still unable to cache data after clearing:', e2);
        }
      }
    }
  }

  // Clear old cache items
  clearOldCache() {
    // Keep only the most important items
    const keysToKeep = ['portfolio-data'];
    
    // Remove other items
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!keysToKeep.includes(key)) {
        localStorage.removeItem(key);
      }
    }
  }
}

// Create global instance
const appLoader = new AppLoader();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  appLoader.init();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = appLoader;
} else {
  window.appLoader = appLoader;
}