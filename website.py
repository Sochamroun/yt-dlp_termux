from flask import Flask, request, render_template_string, send_file, url_for
import yt_dlp
import os
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = "/storage/emulated/0/Movies"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ---------------- HTML MAIN ----------------
HTML = """
<!doctype html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>ទាញយកវីដេអូ</title>
    <style>
:root{color-scheme:dark;--bg:#080d18;--surface:#111c2d;--border:#2a3c55;--text:#eef5ff}
*{box-sizing:border-box}
html{min-height:100%;width:100%;-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;width:100%;padding:max(16px,env(safe-area-inset-top)) max(14px,env(safe-area-inset-right)) max(24px,env(safe-area-inset-bottom)) max(14px,env(safe-area-inset-left));font-family:system-ui,-apple-system,"Noto Sans Khmer",Arial,sans-serif;color:var(--text);text-align:center;background:radial-gradient(ellipse at top,#172b48 0%,var(--bg) 58%)}
h2{margin:12px 0 22px;color:#65e6b3;font-size:clamp(23px,3vw,32px);line-height:1.4}
form{display:flex;flex-direction:column;gap:12px;width:min(100%,620px);margin:18px auto 0;padding:clamp(18px,3vw,30px);background:linear-gradient(145deg,#192a41,#0f1a2a);border:1px solid var(--border);border-radius:20px;box-shadow:0 18px 48px #0005;text-align:left;font-size:16px;line-height:1.7}
form br{display:none}
input[type=text],select{display:block;width:100%;min-height:54px;margin-top:5px;padding:13px 15px;border:1px solid #3b506d;border-radius:13px;background:#0b1422;color:var(--text);font:inherit;font-size:16px;outline:none}
input[type=text]:focus,select:focus{border-color:#65a5ff;box-shadow:0 0 0 3px #2878f033}
input[type=submit],.folder-link,.download-btn,button.reload-btn{display:flex;align-items:center;justify-content:center;width:100%;min-height:56px;padding:13px 18px;margin:8px auto 0;border:0;border-radius:14px;color:white;text-decoration:none;font:inherit;font-size:17px;font-weight:700;cursor:pointer;touch-action:manipulation}
input[type=submit]{background:linear-gradient(135deg,#3289ff,#185bc5)}
.folder-link,.download-btn,button.reload-btn{background:linear-gradient(135deg,#20b978,#13875b)}
.folder-link{width:min(100%,620px);margin:10px auto 18px}
input[type=submit]:active,.folder-link:active,.download-btn:active,button.reload-btn:active{transform:scale(.98)}
.video-preview{display:block;width:100%;max-width:900px;max-height:70vh;height:auto;margin:20px auto 0;border:1px solid var(--border);border-radius:16px;background:#000}
.video-container{display:flex;flex-direction:column;align-items:center;gap:12px;width:100%;margin:22px auto 0}
.download-btn{width:min(100%,520px)}
.error-msg{width:min(100%,620px);margin:20px auto;padding:14px;color:#ffd5d5;background:#471d29;border:1px solid #85364a;border-radius:12px;overflow-wrap:anywhere}
.info{margin:10px auto;color:#ffd66b;font-size:15px}
button.reload-btn{width:min(100%,520px)}
@media(min-width:900px){body{padding-top:36px}form{padding:32px 38px}}
@media(max-width:420px){body{padding-left:12px;padding-right:12px}form{border-radius:16px}h2{margin-bottom:16px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<h2>🌐 ទាញយកវីដេអូ </h2>

<form method="post">
    🔗 URL: <input type="text" name="url" required><br><br>
    📂 Resolution:
    <select name="resolution">
        <option value="144">144p</option>
        <option value="240">240p</option>
        <option value="360">360p</option>
        <option value="480">480p</option>
        <option value="720" selected>720p</option>
        <option value="1080">1080p</option>
    </select><br><br>
    <input type="submit" value="⚡ Download">
</form>

<a href="{{ url_for('list_downloads') }}" class="folder-link">📂 មើលឯកសារ Downloads</a>

{% if error %}
    <div class="error-msg">❌ Error: {{ error }}</div>
{% endif %}

{% if file %}
    <h3>✅ Download Completed:</h3>
    <div class="info">⏳ Time: {{ time_taken }} seconds</div>
    <div class="info">📦 Size: {{ file_size }} MB</div>
    <div class="info">⚡ Speed: {{ speed }} KB/s</div>

    <div class="video-container">
        <video class="video-preview" controls>
            <source src="{{ file }}" type="video/mp4">
        </video>
        <a href="{{ file }}" download class="download-btn">⬇️ Download {{ filename }}</a>
    </div>

    <button class="reload-btn" onclick="window.location.href='/'">🔄 Download New Video</button>
{% endif %}
</body>
</html>
"""

# ---------------- FOLDER VIEW ----------------
FOLDER_HTML = """
<!doctype html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>📂 Downloads Folder</title>
    <style>
:root{color-scheme:dark;--bg:#080d18;--surface:#111c2d;--border:#2a3c55;--text:#eef5ff}
*{box-sizing:border-box}
html{min-height:100%;-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;padding:max(16px,env(safe-area-inset-top)) max(14px,env(safe-area-inset-right)) max(24px,env(safe-area-inset-bottom)) max(14px,env(safe-area-inset-left));background:radial-gradient(ellipse at top,#172b48 0%,var(--bg) 58%);color:var(--text);font-family:system-ui,-apple-system,"Noto Sans Khmer",Arial,sans-serif;text-align:center}
h2{color:#ffd66b;font-size:clamp(23px,3vw,32px);margin:12px 0 24px}
.file-item{display:flex;align-items:center;justify-content:space-between;gap:14px;width:min(100%,980px);margin:12px auto;padding:15px;background:var(--surface);border:1px solid var(--border);border-radius:16px;box-shadow:0 8px 24px #0003;text-align:left}
.file-name{min-width:0;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text);font-size:15px}
.file-actions{display:flex;align-items:center;flex-wrap:nowrap;gap:8px;flex-shrink:0}
.file-actions a,a.back{display:inline-flex;align-items:center;justify-content:center;min-height:50px;padding:11px 14px;border:0;border-radius:12px;color:#fff;text-decoration:none;font-size:15px;font-weight:700;white-space:nowrap;touch-action:manipulation}
.btn-preview{background:#168b5d}.btn-download,a.back{background:#236ed5}
a.back{margin:22px auto 0;min-width:130px}
@media(max-width:600px){.file-item{display:grid;grid-template-columns:minmax(0,1fr);gap:11px;padding:14px}.file-name{width:100%;white-space:nowrap}.file-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;width:100%}.file-actions a{width:100%;min-width:0;padding:10px 6px;font-size:14px}}
@media(min-width:601px) and (max-width:850px){.file-item{gap:8px}.file-actions a{padding:10px 9px;font-size:14px}}
</style>
</head>
<body>
    <h2>📂 File Downloads</h2>
    {% if files %}
        {% for f in files %}
            <div class="file-item">
                <div class="file-name">{{ f }}</div>
                <div class="file-actions">
                    <a href="{{ url_for('preview_video', filename=f) }}" class="btn-preview">▶️ មើលមុន</a>
                    <a href="{{ url_for('download_file', filename=f) }}" class="btn-download">⬇️ Download</a>
                </div>
            </div>
        {% endfor %}
    {% else %}
        <p>❌ មិនទាន់មានឯកសារទេ</p>
    {% endif %}
    <a href="/" class="back">⬅️ Back</a>
</body>
</html>
"""

# ---------------- PREVIEW PAGE (បន្ថែម FILE SIZE) ----------------
PREVIEW_HTML = """
<!doctype html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>🎬 Preview {{ filename }}</title>
    <style>
:root{color-scheme:dark;--bg:#080d18;--text:#eef5ff;--border:#2a3c55}
*{box-sizing:border-box}
html{min-height:100%;-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;padding:max(16px,env(safe-area-inset-top)) max(14px,env(safe-area-inset-right)) max(24px,env(safe-area-inset-bottom)) max(14px,env(safe-area-inset-left));background:radial-gradient(ellipse at top,#172b48 0%,var(--bg) 58%);color:var(--text);text-align:center;font-family:system-ui,-apple-system,"Noto Sans Khmer",Arial,sans-serif}
h2{font-size:clamp(20px,3vw,30px);color:#ffd66b;line-height:1.4;overflow-wrap:anywhere}
p{color:#65e6b3;font-size:16px}
.video-container{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;width:100%;margin:18px auto 0}
video{display:block;width:100%;max-width:1100px;max-height:75vh;height:auto;border:1px solid var(--border);border-radius:16px;background:#000;box-shadow:0 12px 36px #0006}
.download-btn,a.back{display:inline-flex;align-items:center;justify-content:center;min-height:54px;width:min(100%,520px);margin:8px auto 0;padding:12px 18px;border-radius:14px;color:white;text-decoration:none;font-size:17px;font-weight:700;touch-action:manipulation}
.download-btn{background:linear-gradient(135deg,#20b978,#13875b)}
a.back{width:min(100%,220px);background:linear-gradient(135deg,#3289ff,#185bc5)}
@media(min-width:900px){body{padding-top:34px}}
</style>
</head>
<body>
    <h2>🎬 Preview: {{ filename }}</h2>
    <p style="color:#1FD91F; font-size:18px;">📦 File Size: {{ file_size }} MB</p>
    <div class="video-container">
        <video src="{{ url_for('download_file', filename=filename) }}" controls autoplay loop></video>
        <a href="{{ url_for('download_file', filename=filename) }}" class="download-btn">⬇️ Download Video</a>
    </div>
    <a href="{{ url_for('list_downloads') }}" class="back">⬅️ Back</a>
</body>
</html>
"""

# ---------------- MAIN FUNCTIONS ----------------
def download_hook(d):
    pass

@app.route('/', methods=['GET', 'POST'])
def index():
    file_path = None
    filename = None
    error = None
    time_taken = None
    file_size = None
    speed = None

    if request.method == 'POST':
        url = request.form.get('url')
        resolution = request.form.get('resolution', '480')
        start_time = time.time()

        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            title = info.get('title', 'downloaded')
        except Exception as e:
            error = f"Failed to fetch video info: {e}"
            title = 'downloaded'

        safe_title = "".join(
            c if c.isalnum() or c in " ._-" or '\u1780' <= c <= '\u17FF' else "_"
            for c in title
        )
        filename = f"{safe_title}.mp4"
        full_path = os.path.join(DOWNLOAD_FOLDER, filename)

        if not os.path.exists(full_path):
            ydl_opts = {
    'format': f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/mp4",

    # = -S "vcodec:h264,lang,quality,res,fps,hdr:12,acodec:aac"
    'format_sort': [
        'vcodec:h264',
        'lang',
        'quality',
        'res',
        'fps',
        'hdr:12',
        'acodec:aac'
    ],

    # = --merge-output-format mp4
    'merge_output_format': 'mp4',

    # = --remux-video mp4
    'remuxvideo': 'mp4',

    'outtmpl': full_path,
    'progress_hooks': [download_hook],
    'noplaylist': True,
    'quiet': True
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e:
                error = f"Failed to download video: {e}"
                filename = None

        end_time = time.time()
        if os.path.exists(full_path):
            file_path = f"/downloads/{filename}"
            time_taken = round(end_time - start_time, 2)
            size_bytes = os.path.getsize(full_path)
            file_size = round(size_bytes / (1024*1024), 2)
            avg_speed_bytes = size_bytes / max(time_taken, 1)
            speed = round(avg_speed_bytes / 1024, 2)

    return render_template_string(HTML, file=file_path, filename=filename, error=error,
                                  time_taken=time_taken, file_size=file_size, speed=speed)

@app.route('/downloads')
def list_downloads():
    files = os.listdir(DOWNLOAD_FOLDER)
    return render_template_string(FOLDER_HTML, files=files)

@app.route('/downloads/<path:filename>')
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

@app.route('/preview/<path:filename>')
def preview_video(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    size_bytes = os.path.getsize(file_path)
    file_size = round(size_bytes / (1024 * 1024), 2)
    return render_template_string(PREVIEW_HTML, filename=filename, file_size=file_size)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
