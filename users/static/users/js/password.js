document.addEventListener("DOMContentLoaded", function () {
    const togglePasswords = document.querySelectorAll('.toggle-password');

    togglePasswords.forEach(toggle => {
        toggle.addEventListener('click', function () {
            const target = this.getAttribute('data-target');
            const passwordField = document.querySelector(`input[name="${target}"]`);
            const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordField.setAttribute('type', type);
        });
    });
});
