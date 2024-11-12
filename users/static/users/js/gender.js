document.addEventListener('DOMContentLoaded', function () {
    const genderSelect = document.getElementById('id_gender');
    
    genderSelect.addEventListener('change', function () {
        if (this.value === "") {
            this.style.color = 'var(--color-secondary)';
        } else {
            this.style.color = 'var(--color-primary)';
        }
    });

    // Trigger change event to set initial color
    genderSelect.dispatchEvent(new Event('change'));
});
