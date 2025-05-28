class HeaderTemplate {
    constructor() {
      this.headerHTML = `
        <header>
          <nav class="nav">
            <img class="nav-logo" src="https://placehold.co/77x24" alt="Carstensz Logo">
            
            <div class="hamburger">
              <span></span>
              <span></span>
              <span></span>
            </div>
            
            <div class="nav-links">
              <a href="index.html" class="nav-item">Home</a>
              <a href="about.html" class="nav-item">About</a>
              <a href="services.html" class="nav-item">Service</a>
              <a href="portfolio.html" class="nav-item">Portfolio</a>
            </div>
            
            <div class="nav-cta">
              <div class="social-icons">
                <div class="social-icon">
                  <div style="width: 18px; height: 18px; background: #F4F4F4"></div>
                </div>
                <div class="social-icon">
                  <div style="width: 19.50px; height: 19.50px; background: #F4F4F4"></div>
                </div>
                <div class="social-icon">
                  <div style="width: 20px; height: 20px; background: #F4F4F4"></div>
                </div>
              </div>
              <a href="contact.html" class="btn">Contact Us</a>
            </div>
          </nav>
        </header>
      `;
    }
  
    render(selector = 'body') {
      document.querySelector(selector).insertAdjacentHTML('afterbegin', this.headerHTML);
      this.initMobileMenu();
    }
  
    initMobileMenu() {
      const hamburger = document.querySelector('.hamburger');
      const navLinks = document.querySelector('.nav-links');
      
      hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        hamburger.classList.toggle('active');
      });
      
      document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
          navLinks.classList.remove('active');
          hamburger.classList.remove('active');
        });
      });
    }
  }
  
  // Gunakan di semua halaman
  document.addEventListener('DOMContentLoaded', () => {
    const header = new HeaderTemplate();
    header.render();
  });