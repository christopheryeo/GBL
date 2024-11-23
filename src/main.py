"""
Main Flask application file that handles routing, file uploads, and data processing for the Goldbell Leasing web application.
Manages file uploads, data visualization, and serves web pages.
Author: Chris Yeo
"""

from flask import Flask, render_template, request, session, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from ExcelProcessor import ExcelProcessor
from LogManager import LogManager

# Initialize Flask with correct template and static folders
template_dir = os.path.abspath('src/templates')
static_dir = os.path.abspath('src/static')
app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize LogManager
log_manager = LogManager()

@app.route('/')
def index():
    # Clear any existing session data when returning to home
    session.clear()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Clear any existing session data before new upload
    session.clear()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file:
        try:
            # Secure the filename
            filename = secure_filename(file.filename)
            
            # Create the full file path
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(filepath)
            
            # Process the Excel file
            processor = ExcelProcessor()
            success = processor.process_excel(filepath, filename)
            
            if success:
                # Store processed data in session
                session['excel_data'] = {
                    'file_info': processor.get_file_info(),
                    'filepath': filepath
                }
                
                return jsonify({
                    'success': True,
                    'message': 'File successfully uploaded and processed',
                    'file_info': processor.get_file_info()
                })
            else:
                return jsonify({'error': 'Failed to process file'})
            
        except Exception as e:
            return jsonify({'error': str(e)})
    
    return jsonify({'error': 'Invalid file'})

@app.route('/data')
def show_data():
    excel_data = session.get('excel_data')
    return render_template('data.html', excel_data=excel_data)

@app.route('/analytics')
def show_analytics():
    excel_data = session.get('excel_data')
    return render_template('analytics.html', excel_data=excel_data)

@app.route('/chat')
def show_chat():
    excel_data = session.get('excel_data')
    return render_template('chat.html', excel_data=excel_data)

@app.route('/chat_query', methods=['POST'])
def chat_query():
    try:
        # Get the query from the request
        data = request.get_json()
        query = data.get('query', '')
        
        # Get the current excel data from session
        excel_data = session.get('excel_data')
        if not excel_data or 'filepath' not in excel_data:
            return jsonify({
                'response': 'Please upload an Excel file first to analyze the data.'
            })
            
        # Process the query using the ExcelProcessor
        processor = ExcelProcessor()
        processor.process_excel(excel_data['filepath'], '')
        
        # Generate a response based on the query
        # This is a simple example - you can enhance this with more sophisticated analysis
        response = f"Analyzing your question: {query}\n"
        
        if 'total' in query.lower() or 'count' in query.lower():
            file_info = excel_data['file_info']
            if 'processing_info' in file_info:
                total = file_info['processing_info'].get('total_rows', 0)
                response = f"Total number of records: {total}"
        elif 'vehicle' in query.lower():
            # Add vehicle-specific analysis here
            response = "Vehicle information analysis will be available soon."
        else:
            response = "I understand your question. The advanced analysis features will be available soon."
            
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({
            'response': f'Sorry, there was an error processing your request: {str(e)}'
        })

@app.route('/logs')
def show_logs():
    """Show the logs page."""
    return render_template('logs.html')

@app.route('/get_logs')
def get_logs():
    """Get logs after the specified ID."""
    try:
        after_id = int(request.args.get('after_id', -1))
        logs = log_manager.get_logs(after_id)
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8080, debug=True)
    finally:
        log_manager.cleanup()
