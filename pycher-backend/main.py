import os
import google.generativeai as genai
from flask import Flask, request, jsonify
import docker

app = Flask(__name__)
docker_client = docker.from_env()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

@app.route('/execute', methods=['POST'])
def execute_code():
    try:
        code = request.json['code']

        # Run in Docker container
        container = docker_client.containers.run(
            image='python:3.9-slim',
            command=f"python -c '{code}'",
            mem_limit='100m',
            cpu_period=10000,
            cpu_quota=5000,
            detach=True,
            auto_remove=True
        )

        result = container.wait()
        logs = container.logs().decode('utf-8')

        return jsonify({
            "success": result['StatusCode'] == 0,
            "output": logs,
            "error": result['StatusCode'] != 0
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/explain', methods=['POST'])
def explain_code():
    try:
        data = request.json
        prompt = f"""Explain this Python code execution result to a beginner:
        Code: {data['code']}
        { 'Error' if data['error'] else 'Output' }: {data['result']}

        Provide a clear, educational explanation in simple terms.
        Focus on why the {'error occurred' if data['error'] else 'result happened'}.
        Use bullet points if appropriate."""

        response = model.generate_content(prompt)

        return jsonify({
            "explanation": response.text
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
