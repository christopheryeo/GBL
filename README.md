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

### Phase 4: Generic Excel Processing Framework (November 28, 2024)
- Implemented configuration-driven Excel processing
- Added modular processor architecture
- Created format-specific processor system
- Enhanced data validation and transformation

## Project Structure

### Core Python Files
- `main.py`: Main Flask application file handling routing, file uploads, and data processing
- `processors/`: Excel processing framework
  - `base_processor.py`: Abstract base class for Excel processors
  - `processor_factory.py`: Factory for creating format-specific processors
  - `format_specific/`: Format-specific processor implementations
- `config/`: Configuration files
  - `excel_formats.yaml`: Excel format specifications
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
- Configuration-driven Excel format handling
- Modular processor architecture
- Format-specific data processing

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

## Adding Support for New Excel Formats

The application uses a modular, configuration-driven approach for processing different Excel formats. To add support for a new format:

1. **Update Configuration**
   Add your format specification to `src/config/excel_formats.yaml`:
   ```yaml
   formats:
     your_format:
       processor: YourFormatProcessor
       columns:
         - name: "Column1"
           type: "string"
           required: true
         - name: "Column2"
           type: "date"
           required: false
       validations:
         required_columns: ["Column1"]
         date_format: "%Y-%m-%d"
       transformations:
         - clean_data
         - format_dates
   ```

2. **Create Format-Specific Processor**
   Create a new processor in `src/processors/format_specific/your_format.py`:
   ```python
   from ..base_processor import BaseProcessor
   
   class YourFormatProcessor(BaseProcessor):
       def __init__(self):
           super().__init__()
           self.format_config = self.config['formats']['your_format']
           
       def extract_data(self, file_path: str):
           # Implement data extraction logic
           pass
           
       def validate(self, data):
           # Implement validation logic
           pass
           
       def transform(self, data):
           # Implement transformation logic
           pass
   ```

3. **Register the Processor**
   Add your processor to `src/processors/processor_factory.py`:
   ```python
   from .format_specific.your_format import YourFormatProcessor
   
   class ProcessorFactory:
       _processors = {
           'kardex': KardexProcessor,
           'your_format': YourFormatProcessor
       }
   ```

4. **Test the Implementation**
   Use `src/test_processor.py` to verify your implementation:
   ```python
   from processors import ProcessorFactory
   
   # Test with your format
   processor = ProcessorFactory.create('your_format')
   data = processor.process('path/to/your/file.xlsx')
   ```

### Best Practices
- Ensure your processor handles all required columns
- Implement robust error handling
- Add appropriate data validation
- Include data cleaning and transformation
- Document format-specific requirements
- Add test cases for your processor

### Example
See `src/processors/format_specific/kardex.py` for a complete implementation example.
