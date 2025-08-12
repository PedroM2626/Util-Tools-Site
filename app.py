#!/usr/bin/env python3

print("Starting Flask app...", flush=True)

from flask import Flask, render_template, request, redirect, url_for, send_file, after_this_request
from PIL import Image
import os, io, tempfile, subprocess, asyncio

# Try importing all required modules
try:
    from pytube import YouTube
    import pytube.request
    PYTUBE_AVAILABLE = True
    print("pytube: OK", flush=True)
    # Apply patch for pytube
    pytube.request.default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
except ImportError as e:
    print(f"pytube not available: {e}", flush=True)
    PYTUBE_AVAILABLE = False

try:
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
    print("moviepy: OK", flush=True)
except ImportError as e:
    print(f"moviepy not available: {e}", flush=True)
    MOVIEPY_AVAILABLE = False

print("Attempting to import yt_dlp...", flush=True)
try:
    from yt_dlp import YoutubeDL
    YT_DLP_AVAILABLE = True
    print("yt_dlp: OK", flush=True)
except ImportError as e:
    print(f"yt_dlp not available: {e}", flush=True)
    YT_DLP_AVAILABLE = False

print("Attempting to import pytesseract...", flush=True)
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    print("pytesseract: OK", flush=True)
except ImportError as e:
    print(f"pytesseract not available: {e}", flush=True)
    TESSERACT_AVAILABLE = False

try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
    print("rembg: OK", flush=True)
except ImportError as e:
    print(f"rembg not available: {e}", flush=True)
    REMBG_AVAILABLE = False
    rembg_remove = None

print("Creating Flask app...", flush=True)
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

print("Flask app configured", flush=True)

@app.route('/')
def index():
    return render_template('index.html')

# Rota para Music Downloader (/mdcr) – SoundCloud
@app.route('/mdcr', methods=['GET', 'POST'])
def mdcr():
    mensagem = None
    if request.method == 'POST':
        if not YT_DLP_AVAILABLE:
            mensagem = "Funcionalidade não disponível - yt_dlp não instalado"
            return render_template('mdcr.html', mensagem=mensagem)
            
        url = request.form['url']
        if not url or not url.strip():
            mensagem = "Por favor, insira uma URL válida"
            return render_template('mdcr.html', mensagem=mensagem)
            
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(tmpdirname, '%(title)s.%(ext)s'),
                    'socket_timeout': 30,  # Timeout para conexões
                    'retries': 3,          # Número de tentativas em caso de falha
                }
                with YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=True)
                        arquivo_final = ydl.prepare_filename(info)
                    except Exception as e:
                        if "HTTP Error 429" in str(e):
                            mensagem = "Erro: Muitas requisições. Tente novamente mais tarde."
                        elif "urlopen error" in str(e) or "timed out" in str(e):
                            mensagem = "Erro de conexão: Verifique sua internet ou tente novamente mais tarde."
                        else:
                            mensagem = f"Erro ao baixar: {str(e)}"
                        return render_template('mdcr.html', mensagem=mensagem)
                
                try:
                    with open(arquivo_final, 'rb') as f:
                        file_data = io.BytesIO(f.read())
                    file_data.seek(0)
                    return send_file(file_data, as_attachment=True, download_name=os.path.basename(arquivo_final))
                except FileNotFoundError:
                    mensagem = "Erro: Arquivo não encontrado após o download"
                except IOError as e:
                    mensagem = f"Erro ao processar o arquivo: {str(e)}"
        except Exception as e:
            if "urlopen error" in str(e) or "timed out" in str(e) or "ConnectionError" in str(e):
                mensagem = "Erro de conexão: Verifique sua internet ou tente novamente mais tarde."
            else:
                mensagem = f"Erro: {str(e)}"
    return render_template('mdcr.html', mensagem=mensagem)

@app.route('/inscon', methods=['GET', 'POST'])
def inscon():
    mensagem = None
    if request.method == 'POST':
        if not YT_DLP_AVAILABLE:
            mensagem = "Funcionalidade não disponível - yt_dlp não instalado"
            return render_template('inscon.html', mensagem=mensagem)
            
        url = request.form['url']
        if not url or not url.strip():
            mensagem = "Por favor, insira uma URL válida"
            return render_template('inscon.html', mensagem=mensagem)
            
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': os.path.join(tmpdirname, '%(title)s.%(ext)s'),
                    'socket_timeout': 30,  # Timeout para conexões
                    'retries': 3,          # Número de tentativas em caso de falha
                }
                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        nome_arquivo = ydl.prepare_filename(info)
                except Exception as e:
                    if "HTTP Error 429" in str(e):
                        mensagem = "Erro: Muitas requisições. Tente novamente mais tarde."
                    elif "urlopen error" in str(e) or "timed out" in str(e):
                        mensagem = "Erro de conexão: Verifique sua internet ou tente novamente mais tarde."
                    elif "This URL is not supported" in str(e):
                        mensagem = "Erro: Esta URL do Instagram não é suportada. Verifique se é um post público."
                    else:
                        mensagem = f"Erro ao baixar: {str(e)}"
                    return render_template('inscon.html', mensagem=mensagem)
                
                try:
                    arquivo_final = os.path.join(tmpdirname, os.path.basename(nome_arquivo))
                    with open(arquivo_final, 'rb') as f:
                        file_data = io.BytesIO(f.read())
                    file_data.seek(0)
                    return send_file(file_data, as_attachment=True, download_name=os.path.basename(arquivo_final))
                except FileNotFoundError:
                    mensagem = "Erro: Arquivo não encontrado após o download"
                except IOError as e:
                    mensagem = f"Erro ao processar o arquivo: {str(e)}"
        except Exception as e:
            if "urlopen error" in str(e) or "timed out" in str(e) or "ConnectionError" in str(e):
                mensagem = "Erro de conexão: Verifique sua internet ou tente novamente mais tarde."
            else:
                mensagem = f"Erro: {str(e)}"
    return render_template('inscon.html', mensagem=mensagem)

@app.route('/imagermbg', methods=['GET', 'POST'])
def imagermbg():
    mensagem = None
    imagem_sem_fundo = None
    if request.method == 'POST':
        if not REMBG_AVAILABLE:
            mensagem = "Funcionalidade não disponível - rembg não instalado"
            return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=None)
            
        if 'imagem' not in request.files:
            mensagem = "Nenhum arquivo selecionado"
            return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=None)
            
        arquivo = request.files['imagem']
        if arquivo.filename == '':
            mensagem = "Nenhum arquivo selecionado"
            return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=None)
            
        try:
            # Salvar o arquivo temporariamente
            caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
            nome_arquivo_sem_fundo = 'sem_fundo_' + os.path.splitext(arquivo.filename)[0] + '.png'
            caminho_imagem_sem_fundo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo_sem_fundo)
            
            # Garantir que o diretório de upload existe
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            try:
                arquivo.save(caminho_imagem)
            except Exception as e:
                mensagem = f"Erro ao salvar o arquivo: {str(e)}"
                return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=None)
            
            # Verificar se o arquivo foi salvo corretamente
            if not os.path.exists(caminho_imagem) or os.path.getsize(caminho_imagem) == 0:
                mensagem = "Erro: O arquivo não foi carregado corretamente"
                return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=None)
            
            # Remover fundo
            try:
                imagem = Image.open(caminho_imagem)
                # Verificar se a imagem foi aberta corretamente
                if imagem.mode not in ['RGB', 'RGBA']:
                    imagem = imagem.convert('RGB')
                    
                imagem_sem_fundo = rembg_remove(imagem)
                imagem.close()
                
                # Salvar a imagem processada
                imagem_sem_fundo.save(caminho_imagem_sem_fundo, format="PNG")
                
                # Criar URL para exibição
                imagem_sem_fundo_url = url_for('static', filename=f'uploads/{nome_arquivo_sem_fundo}')
                mensagem = "Fundo removido com sucesso!"
                
                # Limpar arquivo original após processamento
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
                    
                return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=imagem_sem_fundo_url)
            except IOError as e:
                mensagem = f"Erro ao abrir a imagem: {str(e)}"
                # Limpar arquivo temporário
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
                return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=None)
            except Exception as e:
                mensagem = f"Erro ao processar a imagem: {str(e)}"
                # Limpar arquivo temporário
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
                return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=None)
        except Exception as e:
            # Garantir limpeza de arquivos temporários em caso de erro
            if 'caminho_imagem' in locals() and os.path.exists(caminho_imagem):
                os.remove(caminho_imagem)
            if 'caminho_imagem_sem_fundo' in locals() and os.path.exists(caminho_imagem_sem_fundo):
                os.remove(caminho_imagem_sem_fundo)
                
            if "No such file or directory" in str(e):
                mensagem = "Erro: Não foi possível acessar o arquivo"
            elif "Permission denied" in str(e):
                mensagem = "Erro: Permissão negada ao acessar o arquivo"
            elif "memory" in str(e).lower():
                mensagem = "Erro: Memória insuficiente para processar a imagem. Tente uma imagem menor."
            else:
                mensagem = f"Erro: {str(e)}"
    return render_template('imagermbg.html', mensagem=mensagem, imagem_sem_fundo=imagem_sem_fundo)

@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    texto_extraido = None
    mensagem = None
    if request.method == 'POST':
        if not TESSERACT_AVAILABLE:
            mensagem = "Funcionalidade não disponível - pytesseract não instalado"
            return render_template('ocr.html', texto_extraido=None, mensagem=mensagem)
            
        if 'imagem' not in request.files:
            mensagem = "Nenhum arquivo selecionado"
            return render_template('ocr.html', texto_extraido=None, mensagem=mensagem)
            
        arquivo = request.files['imagem']
        if arquivo.filename == '':
            mensagem = "Nenhum arquivo selecionado"
            return render_template('ocr.html', texto_extraido=None, mensagem=mensagem)
            
        try:
            # Salvar o arquivo temporariamente
            caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
            
            # Garantir que o diretório de upload existe
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            try:
                arquivo.save(caminho_imagem)
            except Exception as e:
                mensagem = f"Erro ao salvar o arquivo: {str(e)}"
                return render_template('ocr.html', texto_extraido=None, mensagem=mensagem)
            
            # Verificar se o arquivo foi salvo corretamente
            if not os.path.exists(caminho_imagem) or os.path.getsize(caminho_imagem) == 0:
                mensagem = "Erro: O arquivo não foi carregado corretamente"
                return render_template('ocr.html', texto_extraido=None, mensagem=mensagem)
            
            try:
                imagem = Image.open(caminho_imagem)
                texto_extraido = pytesseract.image_to_string(imagem, lang='por')
                imagem.close()
            except IOError as e:
                mensagem = f"Erro ao abrir a imagem: {str(e)}"
                # Limpar arquivo temporário
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
                return render_template('ocr.html', texto_extraido=None, mensagem=mensagem)
            except pytesseract.TesseractError as e:
                mensagem = f"Erro no Tesseract OCR: {str(e)}"
                # Limpar arquivo temporário
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
                return render_template('ocr.html', texto_extraido=None, mensagem=mensagem)
            finally:
                # Limpar arquivo temporário
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
            
            if not texto_extraido or texto_extraido.strip() == '':
                mensagem = "Nenhum texto foi detectado na imagem."
        except Exception as e:
            # Garantir limpeza de arquivos temporários em caso de erro
            if 'caminho_imagem' in locals() and os.path.exists(caminho_imagem):
                os.remove(caminho_imagem)
                
            if "No such file or directory" in str(e):
                mensagem = "Erro: Não foi possível acessar o arquivo"
            elif "Permission denied" in str(e):
                mensagem = "Erro: Permissão negada ao acessar o arquivo"
            elif "TesseractNotFoundError" in str(e):
                mensagem = "Erro: Tesseract OCR não encontrado. Verifique a instalação."
            else:
                mensagem = f"Erro: {str(e)}"
    return render_template('ocr.html', texto_extraido=texto_extraido, mensagem=mensagem)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/ytc', methods=['GET', 'POST'])
def ytc():
    mensagem = None
    if request.method == 'POST':
        if not YT_DLP_AVAILABLE:
            mensagem = "Funcionalidade não disponível - yt_dlp não instalado"
            return render_template('ytc.html', mensagem=mensagem)
            
        url = request.form['url']
        if not url or not url.strip():
            mensagem = "Por favor, insira uma URL válida"
            return render_template('ytc.html', mensagem=mensagem)
            
        formato = request.form['formato']
        qualidade = request.form.get('qualidade', 'best')
        
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Configurações comuns para todas as opções
                common_opts = {
                    'outtmpl': os.path.join(tmpdirname, '%(title)s.%(ext)s'),
                    'socket_timeout': 30,  # Timeout para conexões
                    'retries': 3,          # Número de tentativas em caso de falha
                    'ignoreerrors': False,  # Não ignorar erros
                }
                
                if formato == 'mp3':
                    ydl_opts = {
                        **common_opts,
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    }
                elif formato == 'mp4':
                    ydl_opts = {
                        **common_opts,
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
                    }
                else:
                    ydl_opts = {
                        **common_opts,
                        'format': qualidade,
                    }
                
                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        # Primeiro verificamos se o vídeo existe e está disponível
                        try:
                            info = ydl.extract_info(url, download=False)
                            if not info:
                                mensagem = "Erro: Não foi possível obter informações do vídeo"
                                return render_template('ytc.html', mensagem=mensagem)
                                
                            # Agora fazemos o download
                            ydl.download([url])
                            nome_arquivo = ydl.prepare_filename(info)
                            
                            # Ajuste para o caso de mp3 (o nome do arquivo pode mudar após o processamento)
                            if formato == 'mp3' and not nome_arquivo.endswith('.mp3'):
                                nome_base = os.path.splitext(nome_arquivo)[0]
                                nome_arquivo = f"{nome_base}.mp3"
                                
                        except Exception as e:
                            if "HTTP Error 429" in str(e):
                                mensagem = "Erro: Muitas requisições. Tente novamente mais tarde."
                            elif "urlopen error" in str(e) or "timed out" in str(e):
                                mensagem = "Erro de conexão: Verifique sua internet ou tente novamente mais tarde."
                            elif "This video is unavailable" in str(e) or "Video unavailable" in str(e):
                                mensagem = "Erro: Este vídeo não está disponível ou é privado."
                            elif "Sign in to confirm your age" in str(e) or "age-restricted" in str(e):
                                mensagem = "Erro: Este vídeo tem restrição de idade e não pode ser baixado."
                            elif "The uploader has not made this video available" in str(e):
                                mensagem = "Erro: O uploader não disponibilizou este vídeo para seu país."
                            else:
                                mensagem = f"Erro ao baixar: {str(e)}"
                            return render_template('ytc.html', mensagem=mensagem)
                    
                    try:
                        arquivo_final = os.path.join(tmpdirname, os.path.basename(nome_arquivo))
                        if not os.path.exists(arquivo_final):
                            mensagem = "Erro: Arquivo não encontrado após o download"
                            return render_template('ytc.html', mensagem=mensagem)
                            
                        with open(arquivo_final, 'rb') as f:
                            file_data = io.BytesIO(f.read())
                        file_data.seek(0)
                        return send_file(file_data, as_attachment=True, download_name=os.path.basename(arquivo_final))
                    except FileNotFoundError:
                        mensagem = "Erro: Arquivo não encontrado após o download"
                    except IOError as e:
                        mensagem = f"Erro ao processar o arquivo: {str(e)}"
                except Exception as e:
                    mensagem = f"Erro durante o processamento: {str(e)}"
        except Exception as e:
            if "urlopen error" in str(e) or "timed out" in str(e) or "ConnectionError" in str(e):
                mensagem = "Erro de conexão: Verifique sua internet ou tente novamente mais tarde."
            else:
                mensagem = f"Erro: {str(e)}"
    return render_template('ytc.html', mensagem=mensagem)

@app.route('/mptmp', methods=['GET', 'POST'])
def mptmp():
    mensagem = None
    if request.method == 'POST':
        if not MOVIEPY_AVAILABLE:
            mensagem = "Funcionalidade não disponível - moviepy não instalado"
            return render_template('mptmp.html', mensagem=mensagem)
            
        if 'arquivo' not in request.files:
            mensagem = "Nenhum arquivo selecionado"
            return render_template('mptmp.html', mensagem=mensagem)
            
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            mensagem = "Nenhum arquivo selecionado"
            return render_template('mptmp.html', mensagem=mensagem)
            
        # Verificar extensão do arquivo
        if not arquivo.filename.lower().endswith('.mp4'):
            mensagem = "Formato de arquivo não suportado. Use MP4."
            return render_template('mptmp.html', mensagem=mensagem)
            
        try:
            # Salvar o arquivo temporariamente
            caminho_mp4 = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
            caminho_mp3 = os.path.splitext(caminho_mp4)[0] + '.mp3'
            
            # Garantir que o diretório de upload existe
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            try:
                arquivo.save(caminho_mp4)
            except Exception as e:
                mensagem = f"Erro ao salvar o arquivo: {str(e)}"
                return render_template('mptmp.html', mensagem=mensagem)
            
            # Verificar se o arquivo foi salvo corretamente
            if not os.path.exists(caminho_mp4) or os.path.getsize(caminho_mp4) == 0:
                mensagem = "Erro: O arquivo não foi carregado corretamente"
                return render_template('mptmp.html', mensagem=mensagem)
            
            # Converter para MP3
            try:
                video = VideoFileClip(caminho_mp4)
                video.audio.write_audiofile(caminho_mp3, logger=None)  # Desativar logs excessivos
                video.close()
            except OSError as e:
                mensagem = f"Erro ao processar o arquivo de vídeo: {str(e)}"
                # Limpar arquivo temporário
                if os.path.exists(caminho_mp4):
                    os.remove(caminho_mp4)
                return render_template('mptmp.html', mensagem=mensagem)
            except Exception as e:
                mensagem = f"Erro na conversão do áudio: {str(e)}"
                # Limpar arquivo temporário
                if os.path.exists(caminho_mp4):
                    os.remove(caminho_mp4)
                return render_template('mptmp.html', mensagem=mensagem)
            
            # Verificar se o arquivo MP3 foi criado corretamente
            if not os.path.exists(caminho_mp3) or os.path.getsize(caminho_mp3) == 0:
                mensagem = "Erro: A conversão falhou ao gerar o arquivo MP3"
                # Limpar arquivo temporário
                if os.path.exists(caminho_mp4):
                    os.remove(caminho_mp4)
                return render_template('mptmp.html', mensagem=mensagem)
            
            @after_this_request
            def remove_files(response):
                try:
                    if os.path.exists(caminho_mp4):
                        os.remove(caminho_mp4)
                    if os.path.exists(caminho_mp3):
                        os.remove(caminho_mp3)
                except Exception as e:
                    print(f"Erro ao excluir arquivos temporários: {e}")
                return response
                
            return send_file(caminho_mp3, as_attachment=True, download_name=os.path.basename(caminho_mp3))
        except Exception as e:
            # Garantir limpeza de arquivos temporários em caso de erro
            if 'caminho_mp4' in locals() and os.path.exists(caminho_mp4):
                os.remove(caminho_mp4)
            if 'caminho_mp3' in locals() and os.path.exists(caminho_mp3):
                os.remove(caminho_mp3)
                
            if "No such file or directory" in str(e):
                mensagem = "Erro: Não foi possível acessar o arquivo"
            elif "Permission denied" in str(e):
                mensagem = "Erro: Permissão negada ao acessar o arquivo"
            else:
                mensagem = f"Erro na conversão: {str(e)}"
    return render_template('mptmp.html', mensagem=mensagem)

print("Routes defined", flush=True)

if __name__ == '__main__':
    print("Starting server...", flush=True)
    port = int(os.environ.get('PORT', 5000))
    print(f"Running on port {port}", flush=True)
    app.run(host='0.0.0.0', port=port, debug=True)
