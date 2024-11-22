from flask import Flask, render_template, request, jsonify
from FileRead import handle_file_upload, setup_upload_folder

app = Flask(__name__)

# Set up upload folder when the app starts
setup_upload_folder()

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    result = handle_file_upload(file)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='localhost', port=8080)
