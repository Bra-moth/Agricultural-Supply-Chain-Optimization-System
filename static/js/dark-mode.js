// Dark mode functionality
function initDarkMode() {
    // Check for saved user preference, first in localStorage, then in system setting
    const darkModeStorage = localStorage.getItem('darkMode');
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)');
    
    if (darkModeStorage === 'true' || (darkModeStorage === null && prefersDarkMode.matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.getElementById('darkModeToggle').checked = true;
    }

    // Listen for toggle change
    document.getElementById('darkModeToggle').addEventListener('change', function(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('darkMode', 'true');
        } else {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('darkMode', 'false');
        }
    });

    // Listen for system theme changes
    prefersDarkMode.addEventListener('change', function(e) {
        if (localStorage.getItem('darkMode') === null) {
            if (e.matches) {
                document.documentElement.setAttribute('data-theme', 'dark');
                document.getElementById('darkModeToggle').checked = true;
            } else {
                document.documentElement.removeAttribute('data-theme');
                document.getElementById('darkModeToggle').checked = false;
            }
        }
    });
} 