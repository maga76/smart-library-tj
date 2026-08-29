/**
 * Smart Library TJ — Core UI Scripts
 * Handles layout reactivity, sidebar state, floating AI drawer, notifications
 */

document.addEventListener('DOMContentLoaded', function() {
    // 1. Sidebar Collapse State (Desktop)
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const appWrapper = document.querySelector('.app-wrapper');

    if (sidebarToggleBtn && appWrapper) {
        // Load saved state
        const isCollapsed = localStorage.getItem('smartlib_sidebar_collapsed') === 'true';
        if (isCollapsed && window.innerWidth >= 992) {
            appWrapper.classList.add('sidebar-collapsed');
        }

        sidebarToggleBtn.addEventListener('click', function() {
            if (window.innerWidth >= 992) {
                appWrapper.classList.toggle('sidebar-collapsed');
                localStorage.setItem(
                    'smartlib_sidebar_collapsed',
                    appWrapper.classList.contains('sidebar-collapsed')
                );
            } else {
                appWrapper.classList.toggle('sidebar-open');
            }
        });
    }

    // Mobile sidebar overlay close
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    if (mobileMenuBtn && appWrapper) {
        mobileMenuBtn.addEventListener('click', function() {
            appWrapper.classList.toggle('sidebar-open');
        });
    }

    // 2. Floating AI Assistant «Доно» Drawer
    const donoFabTrigger = document.getElementById('dono-fab-trigger');
    const donoDrawer = document.getElementById('dono-drawer');
    const donoCloseBtn = document.getElementById('dono-close-btn');

    if (donoFabTrigger && donoDrawer) {
        donoFabTrigger.addEventListener('click', function() {
            donoDrawer.classList.toggle('open');
        });
    }

    if (donoCloseBtn && donoDrawer) {
        donoCloseBtn.addEventListener('click', function() {
            donoDrawer.classList.remove('open');
        });
    }

    // 3. Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 6000);
    });

    // 4. Initialize Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
