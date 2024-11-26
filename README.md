# Goldbell Vehicle Maintenance Analytics System

An intelligent web-based application for processing and analyzing vehicle maintenance records, featuring natural language querying capabilities and advanced fault analysis.

**Author: Chris Yeo**

## Overview
This system processes vehicle maintenance records to provide insights into fault patterns, maintenance schedules, and vehicle performance. It uses artificial intelligence to enable natural language queries about maintenance data and automatically categorizes vehicle faults.

## Key Features
- Natural language querying of maintenance data using PandasAI
- Automated fault categorization and analysis
- Flexible Excel data processing with column validation
- Support for multiple vehicle types (14ft, 16ft, 24ft)
- Interactive data visualization
- Comprehensive logging system

## Core Components

### Data Processing
- `VehicleFaults.py`: Core module for processing vehicle maintenance records
  - Flexible column validation
  - Automated fault categorization
  - Robust error handling
  - Data type conversion

### Query Interface
- `PandasChat.py`: Natural language query processing
  - OpenAI integration for query understanding
  - Intelligent data analysis
  - Query result formatting

## Test Framework

### Test Runner (`src/testrunner.py`)
A sophisticated test execution system that provides:
- Sequential test execution with dependency management
- Configurable retry mechanisms and timeouts
- Comprehensive logging and test reporting
- Automatic log file management

### Test Files
- `test_kardex_read.py`: Validates Excel file processing
  - Column validation and data type checking
  - Vehicle type detection
  - Format configuration compliance

- `test_fault_categories.py`: Tests fault categorization
  - Battery fault analysis
  - Fault pattern detection
  - Category validation

- `test_specific_query.py`: Validates query processing
  - Natural language understanding
  - Query result accuracy
  - Response formatting

- `test_chat_queries.py`: Tests chat-based interactions
  - Complex query handling
  - Context management
  - Response generation

### Configuration Files

#### Test Configuration (`src/config/test_config.yaml`)
- Test sequence and dependencies
- Execution settings (retry count, timeouts)
- File paths and mappings
- Test-specific configurations

#### Prompts Configuration (`src/config/prompts.yaml`)
- Query processing guidelines
- Response templates
- Terminology standardization
- Context management rules

#### Fault Categories (`src/config/fault_categories.yaml`)
- Fault category definitions
- Pattern matching rules
- Category hierarchies
- Severity levels

### Logging System

The system maintains detailed logs for each component:

#### Test Runner Log (`logs/test_runner.log`)
- Test execution sequence
- Test results and timing
- Error reports and stack traces
- Overall test summary

#### Kardex Read Log (`logs/kardex_read.log`)
- Excel file processing details
- Data validation results
- Vehicle type detection
- Column mapping status

#### Other Component Logs
- Fault analysis results
- Query processing details
- Performance metrics
- Error diagnostics

### Running Tests

To run the entire test suite with the test runner:
```bash
python -m src.testrunner
```

To run individual test files:
```bash
pytest tests/test_kardex_read.py -v
pytest tests/test_fault_categories.py -v
pytest tests/test_specific_query.py -v
pytest tests/test_chat_queries.py -v
```

## Application Configuration

The system uses several YAML configuration files to manage different aspects of the application:

### Excel Format Configuration (`src/config/test_config.yaml`)
Central configuration file that manages:
- Test file mappings and locations
- Test question configurations and sections
- Excel file configurations
- Logging settings for each test module

### Kardex File Mappings (`src/processors/format_specific/kardex_files.yaml`)
Maps Kardex Excel files to their format specifications:
- Links Excel files to their corresponding format definition files
- Specifies file paths relative to project root
- Used by ProcessorFactory to determine how to process each file

### Format Specifications (`src/processors/format_specific/*.format.yaml`)
Define the structure and validation rules for different Excel formats:
- Row indices for vehicle type, headers, and data
- Column definitions including:
  - Data types (string, float, date)
  - Required/optional status
  - Field descriptions and purposes
- Used by KardexProcessor to correctly parse and validate Excel data

## Dependencies
- Python 3.12+
- PandasAI: Natural language data querying
- OpenAI: Language model integration
- Pandas: Data processing
- Flask: Web interface
- Matplotlib: Data visualization

## Environment Setup
1. Clone the repository
2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Create a `.env` file
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`

## Usage
1. Start the Flask server:
   ```bash
   python src/main.py
   ```
2. Access the web interface at `http://localhost:8080`
3. Upload vehicle maintenance Excel files
4. Use natural language to query your data

## Logging
The system maintains two log files:
- `application.log`: General application events and server activities
- `pandasai.log`: AI query processing and debugging information

## Security Notes
- Keep your `.env` file secure and never commit it to version control
- The system automatically sanitizes sensitive information in logs
- API keys are handled securely through environment variables

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License
Proprietary - All rights reserved
