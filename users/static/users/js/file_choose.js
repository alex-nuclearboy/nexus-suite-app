function updateFileName() {
    const fileInput = document.getElementById("avatar-upload");
    const fileNameDisplay = document.getElementById("file-name");

    if (fileInput.files.length > 0) {
        let fileName = fileInput.files[0].name;

        // Truncate the file name if it is long
        const maxLength = 14;
        if (fileName.length > maxLength) {
            fileName = fileName.slice(0, maxLength) + '...';
        }

        fileNameDisplay.textContent = fileName;
    } else {
        fileNameDisplay.textContent = "{{ translations.no_file_chosen }}";
    }
}