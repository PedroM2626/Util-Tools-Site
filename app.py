from flask import Flask, render_template, request, redirect, url_for, send_file, after_this_request
from PIL import Image
from pytube import YouTube
from moviepy import VideoFileClip
import os, io, tempfile, pytesseract, pytube.request, subprocess, asyncio
from yt_dlp import YoutubeDL

# Try to import rembg, disable feature if not available
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: rembg not available - background removal feature disabled: {e}")
    REMBG_AVAILABLE = False
    rembg_remove = None

# Removemos os imports e instância do Spotdl, pois não usaremos Spotify no site

print("Starting Flask app initialization...")
app = Flask(__name__)
print("Flask app created successfully")

# Configuração do Tesseract (necessário apenas no Windows)
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")

os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/5/tessdata/"

# Pasta para upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Aplica o patch para corrigir o erro 403 no pytube
pytube.request.default_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

@app.route('/')
def index():
    return render_template('index.html')

# Rota para Music Downloader (/mdcr) – agora apenas SoundCloud
@app.route('/mdcr', methods=['GET', 'POST'])
def mdcr():
    mensagem = None
    if request.method == 'POST':
        url = request.form['url']
        # Aqui, removemos a opção "spotify" e mantemos apenas SoundCloud
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Configurações para baixar áudio do SoundCloud usando yt-dlp
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(tmpdirname, '%(title)s.%(ext)s'),
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    arquivo_final = ydl.prepare_filename(info)
                
                with open(arquivo_final, 'rb') as f:
                    file_data = io.BytesIO(f.read())
                file_data.seek(0)
                return send_file(file_data, as_attachment=True, download_name=os.path.basename(arquivo_final))
        except Exception as e:
            mensagem = f"Erro: {str(e)}"
    return render_template('mdcr.html', mensagem=mensagem)

# (As demais rotas permanecem inalteradas)

@app.route('/inscon', methods=['GET', 'POST'])
def inscon():
    mensagem = None
    if request.method == 'POST':
        url = request.form['url']
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': os.path.join(tmpdirname, '%(title)s.%(ext)s'),
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    nome_arquivo = ydl.prepare_filename(info)
                arquivo_final = os.path.join(tmpdirname, os.path.basename(nome_arquivo))
                with open(arquivo_final, 'rb') as f:
                    file_data = io.BytesIO(f.read())
                file_data.seek(0)
                return send_file(file_data, as_attachment=True, download_name=os.path.basename(arquivo_final))
        except Exception as e:
            mensagem = f"Erro: {str(e)}"
    return render_template('inscon.html', mensagem=mensagem)

@app.route('/imagermbg', methods=['GET', 'POST'])
def imagermbg():
    mensagem = None
    imagem_sem_fundo = None
    if request.method == 'POST':
        if 'imagem' not in request.files:
            return redirect(request.url)
        arquivo = request.files['imagem']
        if arquivo.filename == '':
            return redirect(request.url)
        try:
            if not REMBG_AVAILABLE:
                mensagem = "Erro: Funcionalidade de remoção de fundo não disponível. Biblioteca rembg não foi instalada corretamente."
                return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=None)

            caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
            arquivo.save(caminho_imagem)
            imagem = Image.open(caminho_imagem)
            imagem_sem_fundo = rembg_remove(imagem)
            nome_arquivo_sem_fundo = 'sem_fundo_' + os.path.splitext(arquivo.filename)[0] + '.png'
            caminho_imagem_sem_fundo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo_sem_fundo)
            imagem_sem_fundo.save(caminho_imagem_sem_fundo, format="PNG")
            imagem_sem_fundo = url_for('static', filename=f'uploads/{nome_arquivo_sem_fundo}')
            mensagem = "Fundo removido com sucesso!"
        except Exception as e:
            mensagem = f"Erro: {str(e)}"
    return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=imagem_sem_fundo)

@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    texto_extraido = None
    if request.method == 'POST':
        if 'imagem' not in request.files:
            return redirect(request.url)
        arquivo = request.files['imagem']
        if arquivo.filename == '':
            return redirect(request.url)
        caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
        arquivo.save(caminho_imagem)
        imagem = Image.open(caminho_imagem)
        texto_extraido = pytesseract.image_to_string(imagem, lang='por')
    return render_template('ocr.html', texto_extraido=texto_extraido)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/ytc', methods=['GET', 'POST'])
def ytc():
    mensagem = None
    if request.method == 'POST':
        url = request.form['url']
        formato = request.form['formato']
        qualidade = request.form.get('qualidade', 'best')
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                if formato == 'mp3':
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(tmpdirname, '%(title)s.%(ext)s'),
                    }
                elif formato == 'mp4':
                    ydl_opts = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
                        'outtmpl': os.path.join(tmpdirname, '%(title)s.%(ext)s'),
                    }
                else:
                    ydl_opts = {
                        'format': qualidade,
                        'outtmpl': os.path.join(tmpdirname, '%(title)s.%(ext)s'),
                    }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    ydl.download([url])
                    nome_arquivo = ydl.prepare_filename(info)
                arquivo_final = os.path.join(tmpdirname, os.path.basename(nome_arquivo))
                with open(arquivo_final, 'rb') as f:
                    file_data = io.BytesIO(f.read())
                file_data.seek(0)
                return send_file(file_data, as_attachment=True, download_name=os.path.basename(arquivo_final))
        except Exception as e:
            mensagem = f"Erro: {str(e)}"
    return render_template('ytc.html', mensagem=mensagem)

@app.route('/mptmp', methods=['GET', 'POST'])
def mptmp():
    mensagem = None
    if request.method == 'POST':
        if 'arquivo' not in request.files:
            return redirect(request.url)
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return redirect(request.url)
        caminho_mp4 = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
        arquivo.save(caminho_mp4)
        try:
            video = VideoFileClip(caminho_mp4)
            caminho_mp3 = os.path.splitext(caminho_mp4)[0] + '.mp3'
            video.audio.write_audiofile(caminho_mp3)
            video.close()
            @after_this_request
            def remove_files(response):
                try:
                    os.remove(caminho_mp4)
                    os.remove(caminho_mp3)
                except Exception as e:
                    print(f"Erro ao excluir arquivos temporários: {e}")
                return response
            return send_file(caminho_mp3, as_attachment=True, download_name=os.path.basename(caminho_mp3))
        except Exception as e:
            mensagem = f"Erro: {str(e)}"
    return render_template('mptmp.html', mensagem=mensagem)

if __name__ == '__main__':
    print("Starting main execution...")
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on host 0.0.0.0 port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
