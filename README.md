# Goldbell Leasing Data Processing Application

A web-based application for processing and analyzing Excel files, featuring a clean gold-themed user interface.

**Author: Chris Yeo**

## Development Timeline

### Day 1 (November 22, 2024)
- Initial project setup with gold-themed design
- Implemented file upload functionality for PDF and Excel files
- Added specific support for Kardex Excel files
- First UI iteration completed

### Day 2 (November 23, 2024)
- Enhanced UI for data display and consolidation
- Further UI refinements and improvements
- GitHub repository initialization and setup

### Day 3 (November 24, 2024)
- Added comprehensive documentation
- Added author attribution to all files
- Final UI and functionality improvements

## Project Structure

### Python Files
- `main.py`: Main Flask application file that handles routing, file uploads, and data processing. Manages file uploads, data visualization, and serves web pages.
- `ExcelProcessor.py`: Core Excel processing module that handles Excel file parsing, data extraction, and analytics generation. Provides structured data output for visualization and analysis.
- `FileRead.py`: Utility module for file operations, providing functions for secure file reading and validation. Ensures safe handling of uploaded files.

### Templates
- `index.html`: Home page template providing file upload interface with progress tracking and status updates.
- `data.html`: Data visualization template displaying Excel file information, statistics, and interactive charts.
- `analytics.html`: Analytics template providing advanced data analysis and visualization features.

### Static Files
- `style.css`: Consolidated stylesheet providing consistent gold-themed styling, responsive design, and modern UI components.

## Features
- Excel file upload and processing
- Interactive data visualization
- Advanced analytics capabilities
- Responsive, gold-themed UI
- Progress tracking and status updates
- Secure file handling

## Dependencies
- Flask
- Pandas
- Werkzeug
- Openpyxl
- Chart.js

## Installation and Usage
1. Clone the repository
2. Install required Python packages: `pip install -r requirements.txt`
3. Run the application: `python src/main.py`
4. Access the application at `http://localhost:8080`
