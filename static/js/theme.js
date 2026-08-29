/**
 * Smart Library TJ — Light / Dark Theme Toggle
 * Reads/writes localStorage('smartlib_theme') and drives both our own
 * [data-theme] tokens and Bootstrap 5.3's native [data-bs-theme] color mode.
 */
(function () {
    function currentTheme() {
        try {
            var stored = localStorage.getItem('smartlib_theme');
            if (stored === 'dark' || stored === 'light') return stored;
        } catch (e) {}
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        document.documentElement.setAttribute('data-bs-theme', theme);
        document.querySelectorAll('.theme-toggle-icon').forEach(function (icon) {
            icon.className = 'bi theme-toggle-icon ' + (theme === 'dark' ? 'bi-sun' : 'bi-moon-stars');
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        applyTheme(currentTheme());
        document.querySelectorAll('#theme-toggle-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var next = currentTheme() === 'dark' ? 'light' : 'dark';
                try { localStorage.setItem('smartlib_theme', next); } catch (e) {}
                applyTheme(next);
            });
        });
    });
})();
