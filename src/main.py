from flask import Flask, render_template, request, session, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from ExcelProcessor import ExcelProcessor

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
