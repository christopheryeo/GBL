# Goldbell Leasing Data Processing Application

A web-based application for processing and analyzing Excel files, featuring a clean gold-themed user interface and advanced data analysis capabilities.

**Author: Chris Yeo**

## Development Timeline

### Phase 1: Initial Setup and UI (November 22-23, 2024)
- Initial project setup with professional gold-themed design
- Implemented file upload functionality for PDF and Excel files
- Added specific support for Kardex Excel files
- Enhanced UI for data display and consolidation

### Phase 2: Core Features (November 24-25, 2024)
- Added VehicleFault object for structured data handling
- Implemented fault categorization system
- Enhanced data processing capabilities
- Added comprehensive documentation

### Phase 3: Advanced Features (November 26-27, 2024)
- Integrated Chat functionality with ChatGPT
- Added robust error handling
- Implemented real-time system logging
- Enhanced user experience with interactive features

## Project Structure

### Core Python Files
- `main.py`: Main Flask application file handling routing, file uploads, and data processing
- `ExcelProcessor.py`: Core Excel processing module for data extraction and analytics
- `FileRead.py`: Utility module for secure file operations
- `VehicleFault.py`: Object model for vehicle fault data handling
- `ChatGPT.py`: Integration with ChatGPT for intelligent responses
- `LogManager.py`: System-wide logging and monitoring

### Templates
- `index.html`: Home page with file upload interface
- `data.html`: Data visualization and analysis interface
- `analytics.html`: Advanced analytics dashboard
- `chat.html`: Interactive chat interface
- `logs.html`: System logs viewer

### Static Files
- `style.css`: Gold-themed responsive styling
- `script.js`: Client-side interactivity
- `chat.js`: Chat interface functionality

## Features
- Excel file upload and processing
- Interactive data visualization
- Advanced analytics capabilities
- Intelligent chat assistance
- Real-time system logging
- Automatic fault categorization
- Responsive, gold-themed UI
- Progress tracking and status updates
- Secure file handling

## Dependencies
- Flask: Web framework
- Pandas: Data processing
- Werkzeug: File handling
- Openpyxl: Excel processing
- Chart.js: Data visualization
- OpenAI: ChatGPT integration
- Python-dotenv: Environment management

## Installation and Usage
1. Clone the repository
2. Create a `.env` file with required API keys
3. Install required Python packages: `pip install -r requirements.txt`
4. Run the application: `python src/main.py`
5. Access the application at `http://localhost:8080`

## Security Note
Ensure your `.env` file is properly configured with your OpenAI API key and never commit it to version control.
