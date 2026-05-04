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

        const payload = {};
        for (let [key, value] of new FormData(form).entries()) {
            if (key !== 'files[]') payload[key] = value;
        }

        const filesPromises = Array.from(uploadedFiles.files).map(file => {
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve({ name: file.name, data: reader.result });
                reader.readAsDataURL(file);
            });
        });

        Promise.all(filesPromises).then(filesBase64 => {
            payload.files_base64 = filesBase64;

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/deploy_campaign', true);
            xhr.setRequestHeader('Content-Type', 'application/json');

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
                result = { success: false, message: "Server Crash/HTML Returned\n\n" + xhr.responseText.substring(0, 500) };
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

        xhr.send(JSON.stringify(payload));
        
        }).catch(err => {
            alert('Error processing files for upload.');
            finishUpload();
        });

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
    // Profile Command Center Logic
    const profileBtn = document.getElementById('profileBtn');
    const profileDropdown = document.getElementById('profileDropdown');
    const profileContainer = document.getElementById('profileContainer');
    
    if (profileBtn && profileDropdown && profileContainer) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            profileDropdown.style.display = profileDropdown.style.display === 'flex' ? 'none' : 'flex';
        });

        document.addEventListener('click', (e) => {
            if (!profileContainer.contains(e.target)) {
                profileDropdown.style.display = 'none';
            }
        });
    }

    window.createProfile = function() {
        const nameInput = document.getElementById('newProfileName');
        const name = nameInput.value.trim();
        if(!name) return;
        
        const formData = new URLSearchParams();
        formData.append('name', name);
        
        fetch('/api/create_profile', {
            method: 'POST',
            body: formData
        }).then(async res => { const text = await res.text(); try { return JSON.parse(text); } catch(e) { throw new Error('Bad JSON: ' + text.substring(0,100)); } }).then(data => {
            if(data.success) {
                window.location.reload();
            } else {
                alert(data.message || 'Error creating profile');
            }
        }).catch(err => { console.error(err); alert("Network Error: " + err); });
    }

    window.switchProfile = function(id) {
        const formData = new URLSearchParams();
        formData.append('profile_id', id);
        
        fetch('/api/switch_profile', {
            method: 'POST',
            body: formData
        }).then(async res => { const text = await res.text(); try { return JSON.parse(text); } catch(e) { throw new Error('Bad JSON: ' + text.substring(0,100)); } }).then(data => {
            if(data.success) {
                window.location.reload();
            }
        });
    }

    window.saveCredentials = function() {
        const btn = document.getElementById('saveCredsBtn');
        const msg = document.getElementById('saveCredsMsg');
        
        const formData = new URLSearchParams(new FormData(document.getElementById('deployForm')));
        
        btn.disabled = true;
        btn.textContent = 'Saving...';
        
        fetch('/api/save_credentials', {
            method: 'POST',
            body: formData
        }).then(async res => { const text = await res.text(); try { return JSON.parse(text); } catch(e) { throw new Error('Bad JSON: ' + text.substring(0,100)); } }).then(data => {
            btn.disabled = false;
            btn.textContent = 'Save Profile Defaults';
            
            if(data.success) {
                msg.textContent = '✓ Saved securely';
                msg.style.opacity = '1';
                setTimeout(() => { msg.style.opacity = '0'; }, 3000);
            } else {
                alert(data.message || 'Error saving credentials');
            }
        }).catch(err => {
            btn.disabled = false;
            btn.textContent = 'Save Profile Defaults';
            alert("Network Error");
        });
    }

    window.confirmDeleteProfile = function(id, name) {
        document.getElementById('deleteProfileId').value = id;
        document.getElementById('deleteProfileName').textContent = name;
        
        const deleteModal = document.getElementById('deleteProfileModal');
        deleteModal.classList.remove('hidden');
        deleteModal.style.display = 'flex';
        setTimeout(() => {
            deleteModal.classList.add('visible');
        }, 10);
    }
    
    window.closeDeleteModal = function() {
        const deleteModal = document.getElementById('deleteProfileModal');
        deleteModal.classList.remove('visible');
        setTimeout(() => {
            deleteModal.classList.add('hidden');
            deleteModal.style.display = 'none';
        }, 300);
    }
    
    window.executeProfileDeletion = function() {
        const id = document.getElementById('deleteProfileId').value;
        const btn = document.getElementById('confirmDeleteBtn');
        
        btn.disabled = true;
        btn.textContent = 'Deleting...';
        
        const formData = new URLSearchParams();
        formData.append('profile_id', id);
        
        fetch('/api/delete_profile', {
            method: 'POST',
            body: formData
        }).then(async res => {
            const text = await res.text();
            try { return JSON.parse(text); } catch(e) { throw new Error('Bad JSON'); }
        }).then(data => {
            if(data.success) {
                window.location.reload();
            } else {
                alert(data.message || 'Error deleting profile');
                btn.disabled = false;
                btn.textContent = 'Yes, Delete';
                closeDeleteModal();
            }
        }).catch(err => {
            alert("Network Error");
            btn.disabled = false;
            btn.textContent = 'Yes, Delete';
            closeDeleteModal();
        });
    }

    window.openRenameModal = function(id, currentName) {
        document.getElementById('renameProfileId').value = id;
        document.getElementById('renameProfileName').value = currentName;
        
        const renameModal = document.getElementById('renameProfileModal');
        renameModal.classList.remove('hidden');
        renameModal.style.display = 'flex';
        setTimeout(() => {
            renameModal.classList.add('visible');
            document.getElementById('renameProfileName').focus();
        }, 10);
    }
    
    window.closeRenameModal = function() {
        const renameModal = document.getElementById('renameProfileModal');
        renameModal.classList.remove('visible');
        setTimeout(() => {
            renameModal.classList.add('hidden');
            renameModal.style.display = 'none';
        }, 300);
    }
    
    window.executeProfileRename = function() {
        const id = document.getElementById('renameProfileId').value;
        const newName = document.getElementById('renameProfileName').value.trim();
        const btn = document.getElementById('confirmRenameBtn');
        
        if (!newName) {
            alert('Please enter a valid profile name.');
            return;
        }
        
        btn.disabled = true;
        btn.textContent = 'Saving...';
        
        const formData = new URLSearchParams();
        formData.append('profile_id', id);
        formData.append('new_name', newName);
        
        fetch('/api/rename_profile', {
            method: 'POST',
            body: formData
        }).then(async res => {
            const text = await res.text();
            try { return JSON.parse(text); } catch(e) { throw new Error('Bad JSON'); }
        }).then(data => {
            if(data.success) {
                window.location.reload();
            } else {
                alert(data.message || 'Error renaming profile');
                btn.disabled = false;
                btn.textContent = 'Save Changes';
            }
        }).catch(err => {
            alert("Network Error");
            btn.disabled = false;
            btn.textContent = 'Save Changes';
        });
    }
});
