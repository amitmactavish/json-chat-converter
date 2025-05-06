from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import os
import ijson
import csv
import uuid
import traceback

app = Flask(__name__)
app.secret_key = 'secret'
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
MAX_FILE_SIZE_MB = 100

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

chat_messages = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global chat_messages
    chat_messages = []

    if request.method == 'POST':
        file = request.files['json_file']
        if file and file.filename.endswith('.json'):
            file_size = len(file.read()) / (1024 * 1024)
            file.seek(0)

            if file_size > MAX_FILE_SIZE_MB:
                flash(f"File too large! Max {MAX_FILE_SIZE_MB}MB allowed.")
                return redirect(url_for('index'))

            path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{file.filename}")
            file.save(path)

            try:
                with open(path, 'r', encoding='utf-8') as f:
                    parser = ijson.items(f, 'item')
                    for msg in parser:
                        chat_messages.append({
                            "timestamp": msg.get("timestamp", ""),
                            "sender": msg.get("sender", "Unknown"),
                            "text": msg.get("message", "")
                        })
            except Exception as e:
                flash(f"Error parsing JSON: {str(e)}")
                return redirect(url_for('index'))

    return render_template('index.html', messages=chat_messages)

@app.route('/download/<filetype>')
def download(filetype):
    if not chat_messages:
        return redirect(url_for('index'))

    file_path = os.path.join(DOWNLOAD_FOLDER, f'chatlog.{filetype}')

    if filetype == 'txt':
        with open(file_path, 'w', encoding='utf-8') as f:
            for msg in chat_messages:
                f.write(f"[{msg['timestamp']}] {msg['sender']}: {msg['text']}\n")
    elif filetype == 'csv':
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "sender", "text"])
            writer.writeheader()
            writer.writerows(chat_messages)
    else:
        return "Unsupported file type", 400

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

