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

### Testing
- Comprehensive test suite for data processing
- Test cases for natural language queries
- Data validation tests

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
