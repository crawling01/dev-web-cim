// custom-transition.js
document.addEventListener('DOMContentLoaded', function() {
    // Create transition overlay with icon
    const transitionOverlay = document.createElement('div');
    transitionOverlay.className = 'custom-transition-overlay';
    transitionOverlay.innerHTML = `
        <div class="transition-content">
            <i class="fa fa-spinner fa-pulse fa-4x"></i>
            <div class="loading-text">Loading...</div>
        </div>
    `;
    document.body.appendChild(transitionOverlay);
    
    // Add styles dynamically
    const style = document.createElement('style');
    style.textContent = `
        .custom-transition-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(21, 21, 21, 0.95);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .custom-transition-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }
        
        .transition-content {
            text-align: center;
            color: #238CCE;
            transform: translateY(-20px);
            transition: transform 0.3s ease-out;
        }
        
        .custom-transition-overlay.active .transition-content {
            transform: translateY(0);
        }
        
        .fa-spinner {
            margin-bottom: 15px;
            color: #238CCE;
            font-size: 3.5rem;
        }
        
        .loading-text {
            font-family: 'Neue Haas Grotesk Display Pro', sans-serif;
            font-weight: 500;
            letter-spacing: 1px;
            animation: fadeInOut 1.5s infinite alternate;
        }
        
        @keyframes fadeInOut {
            0% { opacity: 0.6; }
            100% { opacity: 1; }
        }
    `;
    document.head.appendChild(style);

    // Enhanced transition handler
    function handleTransition(e) {
        const link = e.target.closest('a');
        if (!link) return;
        
        // Skip special links
        if (link.href.includes('#') || 
            link.target === '_blank' || 
            link.hasAttribute('download') ||
            !link.href.startsWith(window.location.origin)) {
            return;
        }
        
        e.preventDefault();
        
        // Start transition
        transitionOverlay.style.display = 'flex';
        setTimeout(() => {
            transitionOverlay.classList.add('active');
        }, 10);
        
        // Navigate after animation
        setTimeout(() => {
            window.location.href = link.href;
        }, 500);
    }

    // Cleanup on page load
    function cleanupTransition() {
        transitionOverlay.classList.remove('active');
        setTimeout(() => {
            transitionOverlay.style.display = 'none';
        }, 400);
    }

    // Event listeners with better handling
    document.addEventListener('click', handleTransition, { capture: true });
    window.addEventListener('load', cleanupTransition);

    // Ensure Font Awesome is loaded
    if (!document.querySelector('link[href*="font-awesome"]')) {
        const faLink = document.createElement('link');
        faLink.rel = 'stylesheet';
        faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css';
        document.head.appendChild(faLink);
    }
});