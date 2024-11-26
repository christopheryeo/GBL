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

## System Architecture

### Data Processing Pipeline
```
Excel File → FileRead → ExcelProcessor → VehicleFaults → PandasChat → User Interface
             ↓          ↓               ↓              ↓
             Logs  →  Validation  →  Analysis  →    Query Processing
```

1. **Data Ingestion**
   - Excel files processed through `FileRead` and `ExcelProcessor`
   - Format-specific processors handle different Excel layouts
   - Validation against predefined schemas in YAML configs

2. **Fault Analysis**
   - `VehicleFaults` processes maintenance records
   - Categorization based on `fault_categories.yaml`
   - Pattern matching for fault identification
   - Statistical analysis of fault frequencies

3. **Query Processing**
   - Natural language understanding via `PandasChat`
   - Context management for multi-turn conversations
   - Response formatting and validation
   - Integration with OpenAI for query interpretation

### Component Dependencies
- `FileRead` → `ExcelProcessor` → `VehicleFaults`
- `PandasChat` → `QueryPreProcessor` → `ResponseProcessor`
- `ChatGPT` → `PandasChat` for natural language processing
- `LogManager` used by all components

## Development Guidelines

### Adding New Features

1. **Excel Format Support**
   - Create format YAML in `src/processors/format_specific/`
   - Add format mapping to `kardex_files.yaml`
   - Implement format-specific processor if needed
   - Update tests in `test_kardex_read.py`

2. **Fault Categories**
   - Add patterns to `fault_categories.yaml`
   - Update `VehicleFaults.py` categorization logic
   - Add test cases in `test_fault_categories.py`
   - Validate with real maintenance data

3. **Query Capabilities**
   - Add query patterns to `prompts.yaml`
   - Update `QueryPreProcessor.py` if needed
   - Add test cases in `test_specific_query.py`
   - Validate with `test_chat_queries.py`

### Testing Strategy

1. **Unit Tests**
   - Test individual components in isolation
   - Mock external dependencies
   - Focus on edge cases and error conditions
   - Use pytest fixtures for common setup

2. **Integration Tests**
   - Test component interactions
   - Validate data flow through pipeline
   - Check error handling between components
   - Verify logging and monitoring

3. **System Tests**
   - End-to-end workflow validation
   - Performance testing under load
   - Data consistency checks
   - User interface testing

### Logging Guidelines

1. **Component Logs**
   - Use component-specific log files
   - Include timestamp and context
   - Log both success and failure paths
   - Add trace IDs for request tracking

2. **Log Levels**
   - ERROR: System failures
   - WARNING: Potential issues
   - INFO: Normal operations
   - DEBUG: Detailed troubleshooting

## Performance Considerations

### Data Processing
- Batch processing for large Excel files
- Caching of processed results
- Efficient pandas operations
- Memory management for large datasets

### Query Processing
- Response time optimization
- Query result caching
- Rate limiting for API calls
- Connection pooling

### Web Interface
- Asset optimization
- Session management
- Browser caching
- Response compression

## Troubleshooting Guide

### Common Issues

1. **Excel Processing**
   - Check file format in `kardex_files.yaml`
   - Verify column mappings
   - Check file permissions
   - Review validation logs

2. **Query Processing**
   - Check OpenAI API status
   - Verify query patterns in `prompts.yaml`
   - Review query preprocessing logs
   - Check response formatting

3. **Test Failures**
   - Check test dependencies
   - Verify test data availability
   - Review test logs
   - Check configuration settings

### Debug Process
1. Check component-specific logs
2. Review system configuration
3. Verify data integrity
4. Test component in isolation
5. Check external dependencies

## Dependencies
- Python 3.12+
- PandasAI: Natural language data querying
- OpenAI: Language model integration
- Pandas: Data processing
- Flask: Web interface
- Matplotlib: Data visualization

## Project Structure

```
GBL/
├── src/                    # Source code
│   ├── config/            # Configuration files and managers
│   ├── processors/        # Excel file processors
│   ├── static/            # Web assets (CSS, JS, images)
│   ├── templates/         # HTML templates
│   ├── ChatGPT.py        # OpenAI integration
│   ├── ExcelProcessor.py # Excel file processing
│   ├── FileRead.py       # File I/O operations
│   ├── LogManager.py     # Logging system
│   ├── PandasChat.py     # Natural language query
│   ├── VehicleFaults.py  # Fault analysis
│   ├── main.py           # Application entry point
│   └── testrunner.py     # Test execution system
│
├── tests/                 # Test suite
│   ├── config/           # Test configurations
│   ├── test_kardex_read.py    # Excel reading tests
│   ├── test_fault_categories.py # Fault analysis tests
│   ├── test_specific_query.py   # Query processing tests
│   └── test_chat_queries.py     # Chat interface tests
│
├── logs/                  # Application logs
│   ├── test_runner.log   # Test execution logs
│   ├── kardex_read.log   # Excel processing logs
│   └── chat_queries.log  # Query processing logs
│
├── uploads/              # User uploaded files
├── exports/              # Generated reports and charts
├── cache/               # Application cache
└── flask_session/       # Web session data
```

### Directory Overview

#### Source Code (`src/`)
- Core application logic and processing modules
- Configuration management and file processors
- Web interface templates and assets
- Test execution framework

#### Tests (`tests/`)
- Comprehensive test suite for all components
- Test configuration and data files
- Specific test cases for each major feature

#### Data and Logs (`logs/, uploads/, exports/`)
- System logs with component-specific files
- User uploaded Excel files
- Generated reports and visualizations

#### Web Application (`flask_session/, cache/`)
- Session management and caching
- Temporary data storage
- Performance optimization

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
