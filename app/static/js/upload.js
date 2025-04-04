// File upload handling with progress tracking
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('file');
    const uploadModal = document.getElementById('uploadModal');
    const uploadProgressContainer = document.getElementById('uploadProgressContainer');
    const uploadBtn = document.getElementById('uploadBtn');
    
    if (!uploadForm || !fileInput) return;
    
    // Create bootstrap modal instance if it exists
    const uploadModalInstance = uploadModal ? new bootstrap.Modal(uploadModal) : null;
    
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const files = fileInput.files;
        if (files.length === 0) return;
        
        // Show upload modal if exists
        if (uploadModalInstance) {
            uploadModalInstance.show();
        }
        
        // Clear previous upload progress
        if (uploadProgressContainer) {
            uploadProgressContainer.innerHTML = '';
        }
        
        const formData = new FormData(uploadForm);
        const xhr = new XMLHttpRequest();
        
        // Time tracking for speed calculation
        let startTime = Date.now();
        let lastLoaded = 0;
        let uploadSpeed = 0;
        let updateInterval;
        
        // Create progress elements for each file
        Array.from(files).forEach(file => {
            const progressDiv = document.createElement('div');
            progressDiv.classList.add('upload-progress');
            progressDiv.id = `progress-${file.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
            
            // File info
            const fileDiv = document.createElement('div');
            fileDiv.classList.add('file-uploading');
            
            const fileName = document.createElement('div');
            fileName.classList.add('file-name');
            fileName.textContent = file.name;
            fileDiv.appendChild(fileName);
            
            const fileSize = document.createElement('div');
            fileSize.classList.add('file-size');
            fileSize.textContent = formatFileSize(file.size);
            fileDiv.appendChild(fileSize);
            
            progressDiv.appendChild(fileDiv);
            
            // Speed display
            const speedDisplay = document.createElement('div');
            speedDisplay.classList.add('upload-speed');
            speedDisplay.textContent = 'Calculating...';
            progressDiv.appendChild(speedDisplay);
            
            // Progress bar
            const progressBar = document.createElement('div');
            progressBar.classList.add('progress');
            
            const progressBarInner = document.createElement('div');
            progressBarInner.classList.add('progress-bar', 'progress-bar-striped', 'progress-bar-animated');
            progressBarInner.setAttribute('role', 'progressbar');
            progressBarInner.setAttribute('aria-valuenow', '0');
            progressBarInner.setAttribute('aria-valuemin', '0');
            progressBarInner.setAttribute('aria-valuemax', '100');
            progressBarInner.style.width = '0%';
            
            progressBar.appendChild(progressBarInner);
            progressDiv.appendChild(progressBar);
            
            if (uploadProgressContainer) {
                uploadProgressContainer.appendChild(progressDiv);
            }
        });
        
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                
                // Update all progress bars (simplified - in a real app you'd track individual files)
                const progressBars = document.querySelectorAll('.progress-bar');
                progressBars.forEach(bar => {
                    bar.style.width = percentComplete + '%';
                    bar.setAttribute('aria-valuenow', percentComplete);
                });
                
                // Calculate upload speed
                const currentTime = Date.now();
                const timeElapsed = (currentTime - startTime) / 1000; // seconds
                
                if (timeElapsed > 0) {
                    // Calculate speed in bytes per second
                    uploadSpeed = (e.loaded - lastLoaded) / timeElapsed;
                    lastLoaded = e.loaded;
                    startTime = currentTime;
                    
                    // Update speed display
                    const speedDisplays = document.querySelectorAll('.upload-speed');
                    speedDisplays.forEach(display => {
                        display.textContent = `Upload speed: ${formatFileSize(uploadSpeed)}/s`;
                    });
                }
            }
        });
        
        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                // Upload completed successfully
                const response = JSON.parse(xhr.responseText);
                
                // Show success message
                showAlert('success', 'Files uploaded successfully!');
                
                // Close modal after short delay
                setTimeout(() => {
                    if (uploadModalInstance) {
                        uploadModalInstance.hide();
                    }
                    
                    // Reload the file list if we're on the files page
                    if (window.location.pathname.includes('/files')) {
                        window.location.reload();
                    }
                }, 1000);
            } else {
                // Upload failed
                showAlert('danger', 'Upload failed: ' + xhr.statusText);
            }
            
            // Reset form and input
            uploadForm.reset();
            clearInterval(updateInterval);
        });
        
        xhr.addEventListener('error', function() {
            showAlert('danger', 'Upload failed. Please try again.');
            clearInterval(updateInterval);
        });
        
        xhr.addEventListener('abort', function() {
            showAlert('warning', 'Upload aborted.');
            clearInterval(updateInterval);
        });
        
        xhr.open('POST', uploadForm.getAttribute('action'), true);
        xhr.send(formData);
        
        // Update speed display every second
        updateInterval = setInterval(() => {
            const speedDisplays = document.querySelectorAll('.upload-speed');
            speedDisplays.forEach(display => {
                display.textContent = `Upload speed: ${formatFileSize(uploadSpeed)}/s`;
            });
        }, 1000);
    });
    
    // Helper function to format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        
        return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Helper function to show alerts
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show', 'mt-3');
        alertDiv.setAttribute('role', 'alert');
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Find a good place to show the alert
        const container = document.querySelector('.content') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    }
}); 