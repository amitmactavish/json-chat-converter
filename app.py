from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import os
import csv
import ijson
import html
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret'
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

chat_messages = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global chat_messages
    chat_messages = []
    if request.method == 'POST':
        try:
            file = request.files['json_file']
            if file and file.filename.endswith('.json'):
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(path)

                with open(path, 'r', encoding='utf-8') as f:
                    parser = ijson.items(f, 'item')
                    for msg in parser:
                        if msg.get('type') != 'Message':
                            continue
                        chat_messages.append({
                            "timestamp": msg.get("timestamp", ""),
                            "sender": msg.get("from", "Unknown"),
                            "text": parse_content(msg.get("content", ""))
                        })
            else:
                flash("Invalid file type. Please upload a .json file.")
        except Exception as e:
            print(f"Error while parsing: {e}")
            flash(f"Error processing file: {e}")
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

def parse_content(content):
    if isinstance(content, dict):
        return html.escape(str(content))
    elif isinstance(content, list):
        return html.escape(" ".join(str(c) for c in content))
    return html.escape(str(content))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

