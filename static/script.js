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

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if(uploadedFiles.files.length === 0) {
            alert('Please select at least one creative.');
            return;
        }

        submitBtn.disabled = true;
        btnLoader.classList.remove('hidden');
        btnText.textContent = 'Deploying via Meta SDK... (Do not close)';

        const formData = new FormData(form);
        formData.delete('files[]');
        for(let file of uploadedFiles.files) {
            formData.append('files[]', file);
        }

        try {
            const response = await fetch('/api/deploy_campaign', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if(response.ok && result.success) {
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
        } catch(error) {
            modalTitle.textContent = "Deployment Failed!";
            modalMessage.textContent = "Network or server error while executing sequence.";
            modalData.textContent = error.toString();
        } finally {
            submitBtn.disabled = false;
            btnLoader.classList.add('hidden');
            btnText.textContent = 'Launch Campaign';
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
});
