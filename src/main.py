from flask import Flask, render_template, request, jsonify
from FileRead import handle_file_upload, setup_upload_folder
from ExcelProcessor import ExcelProcessor
import os

app = Flask(__name__)
excel_processor = None  # Global variable to store the latest Excel processor

# Set up upload folder when the app starts
setup_upload_folder()

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/data')
def show_data():
    if excel_processor and excel_processor.data_info:
        return render_template('data.html', data=excel_processor.data_info)
    return render_template('data.html', data=None)

@app.route('/upload', methods=['POST'])
def upload_file():
    global excel_processor
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    result = handle_file_upload(file)
    
    if result['success'] and file.filename.endswith(('.xlsx', '.xls')):
        # Process Excel file
        excel_processor = ExcelProcessor(os.path.join('uploads', result['filename']))
        result['message'] = excel_processor.process_file()
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
