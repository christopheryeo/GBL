"""
Main Flask application file that handles routing, file uploads, and data processing for the Goldbell Leasing web application.
Manages file uploads, data visualization, and serves web pages.
Author: Chris Yeo
"""

from flask import Flask, render_template, request, session, jsonify, send_from_directory
from flask_session import Session
import os
from werkzeug.utils import secure_filename
from ExcelProcessor import ExcelProcessor
from LogManager import LogManager
from datetime import timedelta
from pandasai.llm.openai import OpenAI
from pandasai import SmartDataframe
import pandas as pd
from dotenv import load_dotenv
from VehicleFaults import VehicleFault

# Load environment variables from .env file
load_dotenv()

# Initialize Flask with correct template and static folders
template_dir = os.path.abspath('src/templates')
static_dir = os.path.abspath('src/static')
app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)

# Configure Flask-Session
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flask_session')
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Ensure session directory exists
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])

# Initialize Flask-Session
Session(app)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize LogManager
try:
    log_manager = LogManager()
except Exception as e:
    print(f"Error initializing LogManager: {str(e)}")
    raise

@app.route('/')
def index():
    # Clear any existing session data when returning to home
    session.clear()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            log_manager.log("Error: File upload failed - No file part in request")
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            log_manager.log("Error: File upload failed - No selected file")
            return jsonify({'error': 'No selected file'})
        
        if file:
            log_manager.log(f"File upload started: {file.filename}")
            
            # Secure the filename
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(file_path)
            log_manager.log(f"File saved successfully: {filename}")
            
            # Process Excel file
            processor = ExcelProcessor(log_manager)  # Pass log_manager in constructor
            result = processor.process_excel(file_path, filename)
            
            if result:
                # Store data in session
                session['excel_data'] = result
                log_manager.log(f"Stored data in session: {list(result.keys())}")
                return jsonify({'success': True})
            else:
                log_manager.log(f"Error: File processing failed for {filename}")
                return jsonify({'error': 'Failed to process file'})
                
    except Exception as e:
        log_manager.log(f"Error during file upload and processing: {str(e)}")
        return jsonify({'error': str(e)})
    
    return jsonify({'error': 'Invalid file'})

@app.route('/data')
def show_data():
    try:
        log_manager.log("Attempting to retrieve excel_data from session")
        excel_data = session.get('excel_data')
        
        if excel_data:
            log_manager.log(f"Retrieved excel_data from session. Keys present: {list(excel_data.keys())}")
            log_manager.log(f"File info present: {bool(excel_data.get('file_info'))}")
            log_manager.log(f"Data records present: {bool(excel_data.get('data'))}")
            if excel_data.get('data'):
                log_manager.log(f"Number of data records: {len(excel_data['data'])}")
        else:
            log_manager.log("No excel_data found in session")
            
        return render_template('data.html', excel_data=excel_data)
    except Exception as e:
        log_manager.log(f"Error in show_data route: {str(e)}")
        return render_template('data.html', excel_data=None)

@app.route('/analytics')
def show_analytics():
    excel_data = session.get('excel_data')
    return render_template('analytics.html', excel_data=excel_data)

@app.route('/chat')
def show_chat():
    """Show the chat interface."""
    excel_data = session.get('excel_data')
    return render_template('chat.html', excel_data=excel_data)

@app.route('/chat/query', methods=['POST'])
def chat_query():
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({
                'response': 'Please provide a query.'
            })

        # Get the DataFrame from session
        excel_data = session.get('excel_data')
        if not excel_data or not isinstance(excel_data, dict):
            return jsonify({
                'response': 'No data available. Please upload an Excel file first.'
            })

        # Get the full DataFrame from excel_data['data']
        if 'data' not in excel_data:
            return jsonify({
                'response': 'No data available in the Excel file.'
            })
            
        # Create VehicleFault DataFrame instead of regular pandas DataFrame
        df_data = pd.DataFrame(excel_data['data'])
        
        # Convert date columns to datetime
        date_columns = ['Open Date', 'Done Date', 'Actual Finish Date']
        for col in date_columns:
            if col in df_data.columns:
                df_data[col] = pd.to_datetime(df_data[col], errors='coerce')
        
        df = VehicleFault(df_data)
        log_manager.log(f"Created VehicleFault DataFrame with {len(df)} rows for query: {query}")

        # For maintenance year queries, handle directly
        if any(keyword in query.lower() for keyword in ['year', 'when', 'date']):
            if 'Open Date' in df.columns:
                years = df['Open Date'].dt.year.unique()
                years = sorted([year for year in years if not pd.isna(year)])
                
                response_lines = ['Maintenance occurred in the following years:']
                for year in years:
                    count = len(df[df['Open Date'].dt.year == year])
                    response_lines.append(f"- {int(year)}: {count} maintenance records")
                
                response = '\n'.join(response_lines)
                log_manager.log(f"Generated maintenance years response")
                return jsonify({
                    'response': response
                })

        # For fault category distribution queries, use our built-in method
        if any(keyword in query.lower() for keyword in ['distribution', 'breakdown', 'categories']):
            stats = df.get_fault_statistics()
            categories = stats['fault_categories']
            total = sum(categories.values())
            
            # Format the response
            response_lines = ['Distribution of major fault categories:']
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total) * 100
                response_lines.append(f"- {category}: {count} faults ({percentage:.1f}%)")
            
            response = '\n'.join(response_lines)
            log_manager.log(f"Generated fault category distribution response")
            return jsonify({
                'response': response
            })

        # For other queries, use PandasAI
        llm = OpenAI(api_token=os.getenv('OPENAI_API_KEY'))
        smart_df = SmartDataframe(df, config={
            'llm': llm,
            'custom_methods': [
                df.filter_records,
                df.get_filtered_count,
                df.get_active_faults,
                df.get_vehicle_history,
                df.get_faults_by_category,
                df._categorize_faults,
                df.get_fault_statistics
            ]
        })

        # Query the DataFrame
        try:
            response = smart_df.chat(query)
            log_manager.log(f"Query response: {response}")
            return jsonify({
                'response': str(response)
            })
        except Exception as e:
            log_manager.log(f"PandasAI query error: {str(e)}")
            return jsonify({
                'response': f'Error processing query: {str(e)}'
            })
            
    except Exception as e:
        log_manager.log(f"Chat query error: {str(e)}")
        return jsonify({
            'response': f'Sorry, there was an error processing your request: {str(e)}'
        })

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Clear the log file on startup
    with open('application.log', 'w') as f:
        f.write('')
    
    try:
        log_manager.log("Starting Flask application on host='0.0.0.0', port=8080")
        app.run(host='0.0.0.0', port=8080, debug=True)
    finally:
        log_manager.log("Application shutdown initiated")
        log_manager.cleanup()
