document.addEventListener("DOMContentLoaded", function() {
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    fetch(`/set_timezone/?timezone=${timezone}`, { method: 'GET' });
});
