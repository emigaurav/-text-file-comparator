document.addEventListener('DOMContentLoaded', function() {
    const compareBtn = document.getElementById('compareBtn');
    const validateJsonBtn = document.getElementById('validateJsonBtn');
    const formatJsonBtn = document.getElementById('formatJsonBtn');
    const content1 = document.getElementById('content1');
    const content2 = document.getElementById('content2');
    const results = document.getElementById('results');
    const jsonStatus1 = document.getElementById('json-status-1');
    const jsonStatus2 = document.getElementById('json-status-2');

    compareBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content1: content1.value,
                    content2: content2.value
                })
            });

            const data = await response.json();
            
            // Update statistics
            document.getElementById('added-count').textContent = data.differences.stats.added;
            document.getElementById('removed-count').textContent = data.differences.stats.removed;
            document.getElementById('unchanged-count').textContent = data.differences.stats.unchanged;

            // Update diff content
            const diffContent = document.getElementById('diff-content');
            diffContent.innerHTML = '';

            // Show additions
            data.differences.additions.forEach(line => {
                const div = document.createElement('div');
                div.className = 'diff-line diff-added';
                div.textContent = '+ ' + line;
                diffContent.appendChild(div);
            });

            // Show deletions
            data.differences.deletions.forEach(line => {
                const div = document.createElement('div');
                div.className = 'diff-line diff-removed';
                div.textContent = '- ' + line;
                diffContent.appendChild(div);
            });

            // Show results
            results.style.display = 'block';

            // Update JSON validation status
            updateJsonStatus(jsonStatus1, data.json_validation.file1);
            updateJsonStatus(jsonStatus2, data.json_validation.file2);

        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while comparing the files.');
        }
    });

    validateJsonBtn.addEventListener('click', function() {
        validateJson(content1.value, jsonStatus1);
        validateJson(content2.value, jsonStatus2);
    });

    formatJsonBtn.addEventListener('click', async function() {
        await formatJson(content1);
        await formatJson(content2);
    });

    async function validateJson(content, statusElement) {
        try {
            JSON.parse(content);
            updateJsonStatus(statusElement, { valid: true, message: 'Valid JSON' });
        } catch (e) {
            updateJsonStatus(statusElement, { valid: false, message: e.message });
        }
    }

    async function formatJson(textarea) {
        if (!textarea.value.trim()) return;

        try {
            const response = await fetch('/api/format-json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: textarea.value
                })
            });

            const data = await response.json();
            if (data.success) {
                textarea.value = data.result;
            } else {
                alert('Invalid JSON: ' + data.result);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while formatting JSON.');
        }
    }

    function updateJsonStatus(element, status) {
        element.textContent = status.message;
        element.className = 'badge ' + (status.valid ? 'valid-json' : 'invalid-json');
    }
}); 