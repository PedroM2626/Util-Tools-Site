#!/usr/bin/env python3

print("Starting simplified Flask app...")

from flask import Flask, render_template, request, redirect, url_for, send_file
import os

print("Basic imports successful")

# Try optional imports
try:
    from PIL import Image
    PIL_AVAILABLE = True
    print("PIL: OK")
except ImportError:
    PIL_AVAILABLE = False
    print("PIL: Not available")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    print("pytesseract: OK")
except ImportError:
    TESSERACT_AVAILABLE = False
    print("pytesseract: Not available")

print("Creating Flask app...")
app = Flask(__name__)

# Configuração do Tesseract
if TESSERACT_AVAILABLE:
    pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")
    os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/5/tessdata/"

# Pasta para upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

print("Flask configuration complete")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

# Simple OCR route - only if libraries are available
@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    texto_extraido = None
    mensagem = None
    
    if not (PIL_AVAILABLE and TESSERACT_AVAILABLE):
        mensagem = "Funcionalidade OCR não disponível - bibliotecas necessárias não instaladas"
        return render_template('ocr.html', texto_extraido=None, mensagem=mensagem)
        
    if request.method == 'POST':
        try:
            if 'imagem' not in request.files:
                return redirect(request.url)
            arquivo = request.files['imagem']
            if arquivo.filename == '':
                return redirect(request.url)
            caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
            arquivo.save(caminho_imagem)
            imagem = Image.open(caminho_imagem)
            texto_extraido = pytesseract.image_to_string(imagem, lang='por')
        except Exception as e:
            mensagem = f"Erro: {str(e)}"
            
    return render_template('ocr.html', texto_extraido=texto_extraido, mensagem=mensagem)

print("Routes defined")

if __name__ == '__main__':
    print("Starting server...")
    port = int(os.environ.get('PORT', 5000))
    print(f"Running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
