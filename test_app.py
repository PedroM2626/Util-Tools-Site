#!/usr/bin/env python3
print("Starting minimal Flask app...")

from flask import Flask, render_template
import os

print("Imports successful")

app = Flask(__name__)

print("Flask app created")

@app.route('/')
def index():
    return render_template('index.html')

print("Routes defined")

if __name__ == '__main__':
    print("Starting server...")
    port = int(os.environ.get('PORT', 5000))
    print(f"Running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
