document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const progressBar = document.querySelector('.progress');
    const progressBarInner = document.querySelector('.progress-bar');
    const uploadStatus = document.getElementById('upload-status');
    const currentContent = document.querySelector('#current-content pre');
    const linkedinForm = document.getElementById('linkedin-form');
    const linkedinStatus = document.getElementById('linkedin-status');

    // Handle LinkedIn form submission
    linkedinForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const linkedinUrl = document.getElementById('linkedin-url').value;

        linkedinStatus.textContent = 'Importing profile data...';
        linkedinStatus.className = 'alert alert-info';
        linkedinStatus.classList.remove('d-none');

        try {
            const response = await fetch('/admin/import-linkedin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: linkedinUrl })
            });

            const data = await response.json();
            if (data.success) {
                linkedinStatus.textContent = 'LinkedIn profile imported successfully!';
                linkedinStatus.className = 'alert alert-success';
                loadCurrentContent();
            } else {
                linkedinStatus.textContent = data.error || 'Failed to import profile';
                linkedinStatus.className = 'alert alert-danger';
            }
        } catch (error) {
            linkedinStatus.textContent = 'Error importing profile: ' + error;
            linkedinStatus.className = 'alert alert-danger';
        }
    });

    // Handle drag and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('border-primary');
    }

    function unhighlight(e) {
        dropZone.classList.remove('border-primary');
    }

    // Handle file drop
    dropZone.addEventListener('drop', handleDrop, false);

    // Handle file input change
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFile(file);
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        handleFile(file);
    }

    function handleFile(file) {
        if (file.type !== 'text/plain') {
            showStatus('Please upload a .txt file', 'danger');
            return;
        }

        uploadFile(file);
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        progressBar.classList.remove('d-none');
        progressBarInner.style.width = '0%';
        showStatus('Uploading...', 'info');

        fetch('/admin/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('File uploaded successfully!', 'success');
                loadCurrentContent();
            } else {
                showStatus(data.error || 'Upload failed', 'danger');
            }
        })
        .catch(error => {
            showStatus('Upload failed: ' + error, 'danger');
        })
        .finally(() => {
            progressBar.classList.add('d-none');
        });
    }

    function showStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = `alert alert-${type}`;
        uploadStatus.classList.remove('d-none');
    }

    function loadCurrentContent() {
        fetch('/admin/content')
            .then(response => response.text())
            .then(content => {
                currentContent.textContent = content;
            })
            .catch(error => {
                currentContent.textContent = 'Error loading content: ' + error;
            });
    }

    // Load current content when page loads
    loadCurrentContent();
});