import os

project_files = {
    "python": """from flask import Flask, render_template, request, session, send_file, redirect, url_for, flash
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
import re
import shutil
from werkzeug.utils import secure_filename

# Constants
UPLOAD_FOLDER = "uploads"
MAX_HISTORY = 10  # Limit session history

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def ask_gpt(system_prompt, user_prompt, model="gpt-4.1"):
    messages = session.get("history", [])
    messages.append({"role": "user", "content": user_prompt})
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.3
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"❌ Error communicating with OpenAI: {e}"
    messages.append({"role": "assistant", "content": reply})
    # Limit history length
    session["history"] = messages[-MAX_HISTORY:]
    return reply

def extract_code_blocks(output):
    pattern = r"""",
    "output.txt": """return re.findall(pattern, output, re.DOTALL)

def safe_filename(name, default="output.txt"):
    name = name.strip().replace('\n', '').replace('\r', '')
    name = re.sub(r'[`~!@#$%^&*()=+{}\[\]:;"\'<>,/?\\|]', '_', name)
    if not name or name == "_":
        return default
    return name[:128]

def generate_python_script(code_blocks, output_path):
    lines = ["import os"]
    lines.append("\nproject_files = {")
    for filename, content in code_blocks:
        safe_name = safe_filename(filename)
        lines.append(f'    "{safe_name}": """{content.strip()}""",')
    lines.append("}\n")
    lines.append("for path, content in project_files.items():")
    lines.append("    os.makedirs(os.path.dirname(path), exist_ok=True)")
    lines.append("    with open(path, 'w', encoding='utf-8') as f:")
    lines.append("        f.write(content)")
    lines.append("\nprint('✅ Project files created successfully.')")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    code = ""
    question = ""
    output_zip = None

    if request.method == "POST":
        action = request.form.get("action")
        question = request.form.get("question", "")
        code = request.form.get("code", "")

        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename != "":
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            try:
                uploaded_file.save(filepath)
                with open(filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()
                    code += f"\n\n# Uploaded file content:\n{file_content}"
            except Exception as e:
                flash(f"File upload failed: {e}", "error")

        if action == "generate_tests":
            full_prompt = f"Write Python unit tests for the following code:\n\n{code}"
        elif action == "refactor":
            full_prompt = f"Refactor the following code to improve readability and best practices:\n\n{code}"
        elif action == "generate_script":
            full_prompt = (
                "Generate a project that includes multiple files and folders. "
                "Respond with this format:""",
    "for each file._": """)
        else:
            full_prompt = f"My code:\n""",
    "_n_nQuestion__n_question__": """result = ask_gpt(
            "You're a senior developer assistant. Help clearly.", full_prompt
        )

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        project_dir = os.path.join(app.config["UPLOAD_FOLDER"], f"project_{timestamp}")
        os.makedirs(project_dir, exist_ok=True)

        code_blocks = extract_code_blocks(result)
        seen_filenames = set()

        for filename, content in code_blocks:
            filename_clean = safe_filename(filename, f"output_{timestamp}.txt")
            orig_filename_clean = filename_clean
            counter = 1
            while filename_clean in seen_filenames:
                filename_clean = f"{os.path.splitext(orig_filename_clean)[0]}_{counter}{os.path.splitext(orig_filename_clean)[1]}"
                counter += 1
            seen_filenames.add(filename_clean)
            file_path = os.path.join(project_dir, filename_clean)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip())

        # Generate helper script
        script_path = os.path.join(project_dir, "generate_project.py")
        generate_python_script(code_blocks, script_path)

        # Zip the folder
        zip_path = shutil.make_archive(project_dir, 'zip', project_dir)
        output_zip = os.path.basename(zip_path)

    return render_template(
        "index_tailwind.html",
        result=result,
        code=code,
        question=question,
        output_file=output_zip,
    )

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(file_path):
        flash("File not found.", "error")
        return redirect(url_for("index"))
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')