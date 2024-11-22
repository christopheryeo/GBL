from flask import Flask, request, render_template, jsonify, send_from_directory
import os
from ExcelProcessor import ExcelProcessor
from FileRead import handle_file_upload, setup_upload_folder

app = Flask(__name__, static_folder='static')
excel_processor = None  # Global variable to store the latest Excel processor

# Set up upload folder when the app starts
setup_upload_folder()

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/data')
def data():
    if 'excel_processor' in globals() and excel_processor is not None:
        data_info = excel_processor.get_data_info()
        if data_info:
            return render_template('data.html', excel_data={
                'file_info': data_info['file_info']
            })
    return render_template('data.html', excel_data=None)

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

@app.route('/analytics')
def analytics():
    if 'excel_processor' in globals() and excel_processor is not None:
        data_info = excel_processor.get_data_info()
        if data_info:
            return render_template('analytics.html', excel_data=data_info)
    return render_template('analytics.html', excel_data=None)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
