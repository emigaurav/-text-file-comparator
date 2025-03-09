from flask import Flask, render_template, request, jsonify
import json
import difflib
from datetime import datetime
import os

app = Flask(__name__)

# Only enable debug mode in development
app.debug = os.environ.get('FLASK_ENV') == 'development'

def compare_files(content1, content2):
    """Compare two text contents and return differences"""
    lines1 = content1.splitlines()
    lines2 = content2.splitlines()
    
    differ = difflib.Differ()
    diff_results = list(differ.compare(lines1, lines2))
    
    # Process differences
    changes = {
        'additions': [],
        'deletions': [],
        'unchanged': [],
        'stats': {
            'added': sum(1 for line in diff_results if line.startswith('+ ')),
            'removed': sum(1 for line in diff_results if line.startswith('- ')),
            'unchanged': sum(1 for line in diff_results if line.startswith('  '))
        }
    }
    
    for line in diff_results:
        if line.startswith('+ '):
            changes['additions'].append(line[2:])
        elif line.startswith('- '):
            changes['deletions'].append(line[2:])
        elif line.startswith('  '):
            changes['unchanged'].append(line[2:])
    
    return changes

def validate_json(content):
    """Validate if content is valid JSON"""
    try:
        if not content.strip():
            return False, "Empty content"
        json.loads(content)
        return True, "Valid JSON"
    except json.JSONDecodeError as e:
        return False, str(e)

def format_json(content):
    """Format JSON content with proper indentation"""
    try:
        parsed = json.loads(content)
        return True, json.dumps(parsed, indent=4)
    except json.JSONDecodeError as e:
        return False, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/compare', methods=['POST'])
def compare():
    data = request.json
    content1 = data.get('content1', '')
    content2 = data.get('content2', '')
    
    # Compare files
    differences = compare_files(content1, content2)
    
    # Check JSON validity
    json_valid1, json_msg1 = validate_json(content1)
    json_valid2, json_msg2 = validate_json(content2)
    
    return jsonify({
        'differences': differences,
        'json_validation': {
            'file1': {'valid': json_valid1, 'message': json_msg1},
            'file2': {'valid': json_valid2, 'message': json_msg2}
        }
    })

@app.route('/api/format-json', methods=['POST'])
def format_json_endpoint():
    data = request.json
    content = data.get('content', '')
    success, result = format_json(content)
    
    return jsonify({
        'success': success,
        'result': result
    })

if __name__ == '__main__':
    # Use environment variables for host and port
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 