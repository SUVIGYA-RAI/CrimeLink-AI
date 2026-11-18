/*
 * CrimeLink AI - Main JavaScript
 */

// Auto-hide alert messages after 4 seconds
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 4000);
    });

    // Set active sidebar link based on current URL
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    sidebarLinks.forEach(function (link) {
        if (currentPath.startsWith(link.getAttribute('href'))) {
            link.classList.add('active');
        }
    });

    // Confirm delete actions
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Adaptive Visual Intelligence Network Interaction
    const heroVisual = document.querySelector('.adaptive-hero-visual');
    if (heroVisual) {
        const nodes = heroVisual.querySelectorAll('.node-circle');
        nodes.forEach(function (node) {
            node.addEventListener('mouseenter', function () {
                this.style.transform = 'scale(1.22)';
                this.style.filter = 'drop-shadow(0 0 14px var(--hero-accent))';
            });
            node.addEventListener('mouseleave', function () {
                this.style.transform = '';
                this.style.filter = '';
            });
        });
    }
});
