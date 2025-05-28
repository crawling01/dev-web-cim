document.addEventListener('DOMContentLoaded', function() {
    const gifPath = '/static/transisi.gif';
    const preloadGif = new Image();
    preloadGif.src = gifPath;

    preloadGif.onload = function() {
        createTransitionOverlay(gifPath);
    };

    function createTransitionOverlay(gifPath) {
        const transitionOverlay = document.createElement('div');
        transitionOverlay.className = 'custom-transition-overlay hidden'; // default hidden
        transitionOverlay.innerHTML = `
            <div class="transition-content">
                <img src="${gifPath}?t=${Date.now()}" alt="Loading" class="transition-gif">
            </div>
        `;
        document.body.appendChild(transitionOverlay);

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
                opacity: 1;
                visibility: visible;
                pointer-events: auto;
                transition: opacity 1s cubic-bezier(0.4, 0, 0.2, 1), visibility 1s; /* Diubah dari 0.4s menjadi 1s */
            }
            .custom-transition-overlay.hidden {
                opacity: 0;
                visibility: hidden;
                pointer-events: none;
            }
            .transition-content {
                text-align: center;
                color: #238CCE;
                transform: translateY(0);
                transition: transform 0.6s ease-out; /* Diubah dari 0.3s menjadi 0.6s */
            }
            .custom-transition-overlay.active .transition-content {
                transform: translateY(0);
            }
            .transition-gif {
                width: 150px;
                height: 150px;
                margin-bottom: 15px;
                object-fit: contain;
                image-rendering: optimizeSpeed;
                image-rendering: -moz-crisp-edges;
                image-rendering: -o-crisp-edges;
                image-rendering: -webkit-optimize-contrast;
                image-rendering: crisp-edges;
                image-rendering: pixelated;
                -ms-interpolation-mode: nearest-neighbor;
            }
            .loading-text {
                font-family: 'Neue Haas Grotesk Display Pro', sans-serif;
                font-weight: 500;
                letter-spacing: 1px;
                animation: fadeInOut 2s infinite alternate; /* Diubah dari 1.5s menjadi 2s */
            }
            @keyframes fadeInOut {
                0% { opacity: 0.6; }
                100% { opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        // Transition handler
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a');
            if (!link) return;
            if (link.href.includes('#') || link.target === '_blank' || link.hasAttribute('download') || !link.href.startsWith(window.location.origin)) {
                return;
            }
            e.preventDefault();

            // Tampilkan overlay
            transitionOverlay.classList.remove('hidden');
            setTimeout(() => {
                transitionOverlay.classList.add('active');
            }, 10);

            // Navigasi setelah animasi - diubah dari 500ms menjadi 1000ms (1 detik)
            setTimeout(() => {
                window.location.href = link.href;
            }, 1000);
        }, { capture: true });

        // Cleanup di load
        window.addEventListener('load', function() {
            transitionOverlay.classList.remove('active');
            setTimeout(() => {
                transitionOverlay.classList.add('hidden');
            }, 1000); // Diubah dari 400ms menjadi 1000ms (1 detik)
        });
    }
});