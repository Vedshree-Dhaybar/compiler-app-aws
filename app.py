import subprocess
import uuid
import boto3
from flask import Flask, request, jsonify

app = Flask(__name__)
s3 = boto3.client('s3')
BUCKET_NAME = 'my-successful-code-bucket-2026'

@app.route('/run', methods=['POST'])
def run_code():
    data = request.json
    language = data.get('language') # 'python' or 'java'
    code = data.get('code')
    
    filename = f"tmp_{uuid.uuid4().hex}"
    
    try:
        if language == 'python':
            full_file = f"{filename}.py"
            with open(full_file, 'w') as f: f.write(code)
            # Run code safely in a subprocess
            result = subprocess.run(['python3', full_file], capture_output=True, text=True, timeout=5)
            
        elif language == 'java':
            # Java requires the class name to match the filename
            full_file = "Main.java" 
            with open(full_file, 'w') as f: f.write(code)
            subprocess.run(['javac', full_file], capture_output=True, text=True, timeout=5)
            result = subprocess.run(['java', 'Main'], capture_output=True, text=True, timeout=5)
            
        if result.returncode == 0:
            # Code ran successfully -> Store to S3
            s3.put_object(Bucket=BUCKET_NAME, Key=f"successful-runs/{filename}.txt", Body=code)
            return jsonify({'status': 'success', 'output': result.stdout})
        else:
            return jsonify({'status': 'error', 'output': 'errors in code', 'details': result.stderr})
            
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'output': 'errors in code', 'details': 'Timeout limit exceeded'})
    except Exception as e:
        return jsonify({'status': 'error', 'output': 'errors in code', 'details': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
