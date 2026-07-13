import os
import subprocess
import uuid
import boto3
from flask import Flask, request, jsonify, render_template
from botocore.exceptions import NoCredentialsError

app = Flask(__name__)

# AWS S3 Configuration (Ensure your EC2 IAM Role has S3 write permissions)
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "
compiler-app-submissions")
s3_client = boto3.client('s3')

TEMP_DIR = "/tmp/compiler_runs"
os.makedirs(TEMP_DIR, exist_ok=True)

def upload_to_s3(file_path, file_name):
    try:
        s3_client.upload_file(file_path, S3_BUCKET_NAME, file_name)
        return True
    except NoCredentialsError:
        print("AWS Credentials not found or IAM role missing.")
        return False
    except Exception as e:
        print(f"S3 Upload failed: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compile', methods=['POST'])
def compile_code():
    data = request.get_json()
    language = data.get('language')
    code = data.get('code')
    
    if not language or not code:
        return jsonify({'error': 'Missing language or code data'}), 400

    # Create a unique execution ID and file names
    run_id = str(uuid.uuid4())
    
    if language == 'python':
        file_name = f"script_{run_id}.py"
        file_path = os.path.join(TEMP_DIR, file_name)
        with open(file_path, 'w') as f:
            f.write(code)
        
        # Execute Python code safely
        cmd = ["python3", file_path]
        
    elif language == 'java':
        # Java requires class name matching file name. 
        # For simplicity, we expect/force the class to be 'Main'
        file_name = "Main.java"
        run_dir = os.path.join(TEMP_DIR, run_id)
        os.makedirs(run_dir, exist_ok=True)
        file_path = os.path.join(run_dir, file_name)
        
        with open(file_path, 'w') as f:
            f.write(code)
            
        # Compile Java
        compile_cmd = subprocess.run(["javac", file_path], capture_output=True, text=True, timeout=10)
        if compile_cmd.returncode != 0:
            return jsonify({'success': False, 'output': f"errors in code:\n{compile_cmd.stderr}"})
            
        # Execute Java
        cmd = ["java", "-cp", run_dir, "Main"]
    else:
        return jsonify({'error': 'Unsupported language'}), 400

    try:
        # Run code with a timeout limit to prevent infinite loops
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            # Code ran successfully -> Upload to S3
            s3_file_name = f"successful_runs/{language}/{run_id}_{file_name}"
            s3_uploaded = upload_to_s3(file_path, s3_file_name)
            
            return jsonify({
                'success': True, 
                'output': result.stdout,
                's3_saved': s3_uploaded
            })
        else:
            return jsonify({
                'success': False, 
                'output': f"errors in code:\n{result.stderr}"
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'output': 'errors in code: Execution Timeout (Infinite Loop?)'})
    except Exception as e:
        return jsonify({'success': False, 'output': f'errors in code: {str(e)}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
