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
            processor = ExcelProcessor()
            processor.set_log_manager(log_manager)  # Inject the log manager
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
        vehicle_faults = None
        
        if excel_data and isinstance(excel_data, dict) and 'data' in excel_data:
            log_manager.log(f"Retrieved excel_data from session. Keys present: {list(excel_data.keys())}")
            log_manager.log(f"File info present: {bool(excel_data.get('file_info'))}")
            log_manager.log(f"Data records present: {bool(excel_data.get('data'))}")
            
            if excel_data.get('data'):
                data = excel_data['data']
                log_manager.log(f"Number of data records: {len(data)}")
                
                # Get the first sheet's data for vehicle faults
                if isinstance(data, dict) and len(data) > 0:
                    first_sheet_name = list(data.keys())[0]
                    vehicle_faults = data[first_sheet_name]
                    log_manager.log(f"Retrieved vehicle faults from sheet: {first_sheet_name}")
        else:
            log_manager.log("No excel_data found in session")
            
        return render_template('data.html', excel_data=excel_data, vehicle_faults=vehicle_faults)
    except Exception as e:
        log_manager.log(f"Error in show_data route: {str(e)}")
        return render_template('data.html', excel_data=None, vehicle_faults=None)

@app.route('/analytics')
def show_analytics():
    excel_data = session.get('excel_data')
    return render_template('analytics.html', excel_data=excel_data)

@app.route('/chat')
def show_chat():
    """Show the chat interface."""
    return render_template('chat.html')

@app.route('/chat/query', methods=['POST'])
def chat_query():
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({
                'response': 'Please provide a query.'
            })
            
        # Here you would process the query and generate a response
        # For now, we'll just echo back the query
        return jsonify({
            'response': f'You asked: {query}'
        })
        
    except Exception as e:
        return jsonify({
            'response': f'Sorry, there was an error processing your request: {str(e)}'
        })

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    try:
        log_manager.log("Starting Flask application on host='0.0.0.0', port=8080")
        app.run(host='0.0.0.0', port=8080, debug=True)
    finally:
        log_manager.log("Application shutdown initiated")
        log_manager.cleanup()
