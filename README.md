# Text File Comparator

A powerful GUI application for comparing text files and JSON documents with advanced features and optimized performance.

![Text File Comparator](screenshots/app_screenshot.png)

## Features

- 📊 Side-by-side visual comparison of text files
- 🔍 Advanced JSON support:
  - Automatic JSON validation
  - JSON formatting with proper indentation
  - Visual indicators for JSON validity
- 🚀 Performance optimizations:
  - Memory-mapped file reading for large files
  - Multi-threaded operations
  - Batch processing for UI updates
- 📝 Detailed comparison reports:
  - Summary statistics
  - Line-by-line differences
  - JSON validation status
- 💫 Modern UI features:
  - Progress bar for long operations
  - Synchronized scrolling
  - Color-coded differences
  - Horizontal scrolling support

## Requirements

- Python 3.x
- tkinter (usually comes with Python installation)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/text-file-comparator.git
cd text-file-comparator
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python text_file_comparator.py
```

2. Select files for comparison:
   - Click "Browse" buttons to select two files
   - Files can be any text format, including JSON
   - JSON files are automatically validated

3. Use the available features:
   - Click "Compare Files" to see differences
   - Click "Validate JSON" to check JSON validity
   - Click "Format JSON" to prettify JSON content
   - Click "Generate Report" for detailed comparison

## Key Features Explained

### JSON Validation
- Automatic validation when JSON files are loaded
- Visual indicators show validation status:
  - ✅ Green checkmark for valid JSON
  - ❌ Red X for invalid JSON
  - ⚠️ Orange warning for empty files

### Performance Optimizations
- Memory mapping for large files (>10MB)
- Background threading for heavy operations
- Efficient diff algorithm implementation
- Batch processing for UI updates
- Content caching with LRU cache

### Comparison Reports
Reports include:
- Timestamp of comparison
- File paths and JSON validity status
- Number of lines added, removed, and unchanged
- Detailed list of all changes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python and tkinter
- Uses `difflib` for efficient text comparison
- Implements memory mapping for large file handling
- Utilizes threading for responsive UI
