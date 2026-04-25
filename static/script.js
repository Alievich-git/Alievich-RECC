document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('files');
    const fileList = document.getElementById('fileList');
    const form = document.getElementById('deployForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnLoader = document.getElementById('btnLoader');
    const btnText = document.querySelector('.btn-text');
    
    const modal = document.getElementById('resultModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const modalData = document.getElementById('modalData');

    // Auto-resize Primary Text textarea
    const primaryTextarea = document.getElementById('primary_text');
    if (primaryTextarea) {
        primaryTextarea.addEventListener('input', function() {
            this.style.height = 'auto'; // Reset the height
            this.style.height = (this.scrollHeight) + 'px'; // Set it to scroll height
        });
    }

    let uploadedFiles = new DataTransfer();

    // Drag and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        for(let file of files) {
            uploadedFiles.items.add(file);
            
            const chip = document.createElement('div');
            chip.className = 'file-chip';
            chip.innerHTML = `
                <span>${file.name}</span>
                <span style="cursor:pointer;" onclick="removeFile('${file.name}', this)">&times;</span>
            `;
            fileList.appendChild(chip);
        }
        fileInput.files = uploadedFiles.files;
    }

    window.removeFile = function(fileName, element) {
        const dt = new DataTransfer();
        for(let i = 0; i < uploadedFiles.files.length; i++) {
            if(uploadedFiles.files[i].name !== fileName) {
                dt.items.add(uploadedFiles.files[i]);
            }
        }
        uploadedFiles = dt;
        fileInput.files = uploadedFiles.files;
        element.parentElement.remove();
    }

    // Toggle Help texts
    window.toggleHelp = function(id) {
        const el = document.getElementById(id);
        if (el.classList.contains('hidden')) {
            el.classList.remove('hidden');
        } else {
            el.classList.add('hidden');
        }
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if(uploadedFiles.files.length === 0) {
            alert('Please select at least one creative.');
            return;
        }

        submitBtn.disabled = true;
        btnLoader.classList.remove('hidden');
        btnText.textContent = 'Uploading Media... (Do not close)';

        // Setup Progress Bar
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        progressContainer.classList.remove('hidden');
        progressBar.style.width = '0%';
        progressBar.classList.remove('pulse');
        progressText.textContent = '0%';

        const formData = new FormData(form);
        formData.delete('files[]');
        for(let file of uploadedFiles.files) {
            formData.append('files[]', file);
        }

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/deploy_campaign', true);

        xhr.upload.onprogress = function(event) {
            if (event.lengthComputable) {
                // Authentic physical upload tracking for real-world file traversal
                const percentComplete = Math.round((event.loaded / event.total) * 100);
                
                progressBar.style.width = percentComplete + '%';
                progressText.textContent = percentComplete + '%';
                
                if (percentComplete === 100) {
                    btnText.textContent = 'Executing Meta APIs... (Please wait)';
                    progressBar.classList.add('pulse');
                }
            }
        };

        xhr.onload = function() {
            progressBar.classList.remove('pulse');
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            
            let result;
            try {
                result = JSON.parse(xhr.responseText);
            } catch(e) {
                result = { success: false, message: "Invalid JSON response from server." };
            }

            if (xhr.status === 200 && result.success) {
                modalTitle.textContent = "Deployment Successful!";
                modalMessage.textContent = "Your Meta Ads campaign has been completely generated in a PAUSED state.";
                modalData.innerHTML = `
Campaign ID: ${result.data.campaign_id}
Lead Form ID: ${result.data.form_id}
AdSets Generated: ${result.data.adsets_created}
Ad IDs:
${result.data.ad_ids.map(id => `  - ${id}`).join('\n')}
                `;
            } else {
                modalTitle.textContent = "Deployment Failed!";
                modalMessage.textContent = "The internal Meta Ads engine encountered an error.";
                modalData.textContent = result.message || "Unknown error";
            }
            finishUpload();
        };

        xhr.onerror = function() {
            modalTitle.textContent = "Deployment Failed!";
            modalMessage.textContent = "Network or server error while executing sequence.";
            modalData.textContent = "XHR Request Error";
            finishUpload();
        };

        xhr.send(formData);

        function finishUpload() {
            submitBtn.disabled = false;
            btnLoader.classList.add('hidden');
            btnText.textContent = 'Launch Campaign';
            progressBar.classList.remove('pulse');
            progressContainer.classList.add('hidden');
            modal.classList.remove('hidden');
        }
    });

    window.closeModal = function() {
        modal.classList.add('hidden');
        if(modalTitle.textContent === "Deployment Successful!") {
            // Optional: reset form after success
            fileList.innerHTML = '';
            uploadedFiles = new DataTransfer();
            form.reset();
        }
    }

    // Initialize Particles.js background
    if(window.particlesJS) {
        particlesJS("particles-js", {
            "particles": {
                "number": { "value": 60, "density": { "enable": true, "value_area": 800 } },
                "color": { "value": "#23d5d5" },
                "shape": { "type": "circle" },
                "opacity": { "value": 0.3, "random": false },
                "size": { "value": 2, "random": true },
                "line_linked": { "enable": true, "distance": 150, "color": "#23d5d5", "opacity": 0.2, "width": 1 },
                "move": { "enable": true, "speed": 1.5, "direction": "none", "random": true, "straight": false, "out_mode": "out", "bounce": false }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": { "onhover": { "enable": true, "mode": "grab" }, "onclick": { "enable": true, "mode": "push" }, "resize": true },
                "modes": { "grab": { "distance": 140, "line_linked": { "opacity": 0.5 } }, "push": { "particles_nb": 4 } }
            },
            "retina_detect": true
        });
    }
});
