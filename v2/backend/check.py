from flask import request
import os

UPLOAD_FOLDER = 'static/user_uploaded'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the directory exists

# Extract file from the request
if 'file' not in request.files:
    print("No file part in the request")
else:
    file = request.files['file']
    if file.filename == '':
        print("No selected file")
    else:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        print(f"File saved at: {file_path}")
