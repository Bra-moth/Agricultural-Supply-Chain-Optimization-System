// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize all popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide flash messages after 5 seconds
    var flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(flash) {
        setTimeout(function() {
            var alert = new bootstrap.Alert(flash);
            alert.close();
        }, 5000);
    });

    // Add animation class to elements with data-animate attribute
    var animatedElements = document.querySelectorAll('[data-animate]');
    animatedElements.forEach(function(element) {
        element.classList.add('animate-fade-in');
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add active class to current nav item
    var currentLocation = window.location.pathname;
    var navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });

    // Handle mobile menu toggle
    var navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.querySelector('.navbar-collapse').classList.toggle('show');
        });
    }

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        var navbar = document.querySelector('.navbar-collapse');
        var toggleButton = document.querySelector('.navbar-toggler');
        
        if (navbar.classList.contains('show') && 
            !navbar.contains(event.target) && 
            !toggleButton.contains(event.target)) {
            navbar.classList.remove('show');
        }
    });
}); 