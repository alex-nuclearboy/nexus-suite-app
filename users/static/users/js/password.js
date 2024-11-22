// Function to show the password

document.addEventListener("DOMContentLoaded", function () {
    const togglePasswords = document.querySelectorAll('.toggle-password');

    togglePasswords.forEach(function (togglePassword) {
        // Add an event listener for each checkbox
        togglePassword.addEventListener('change', function () {
            const targetId = togglePassword.dataset.target; // Get the password field id
            const passwordField = document.getElementById(targetId); // Find this field by id

            // Switch the password field type between ‘password’ and ‘text’
            if (passwordField) {
                passwordField.type = togglePassword.checked ? 'text' : 'password';
            }
        });
    });
});
