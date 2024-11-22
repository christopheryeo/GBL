import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def setup_upload_folder():
    upload_path = os.path.join(os.getcwd(), UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    return upload_path

def handle_file_upload(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = setup_upload_folder()
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        return {
            'success': True,
            'filename': filename,
            'message': f'File {filename} uploaded successfully'
        }
    return {
        'success': False,
        'message': 'Invalid file type. Only PDF and Excel files are allowed.'
    }
