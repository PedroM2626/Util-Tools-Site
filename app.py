import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import os
import pytesseract
from PIL import Image
import tempfile
import math
import aiohttp
import subprocess
import shutil
import qrcode
from rembg import remove as remove_bg
from urllib.parse import urlparse
from io import BytesIO

TOKEN = "MTMzODU0MjMzMDc3MjE5NzQwNw.G3F7Bi.1hdXdE48dcViz85VMdrtSuHpNanc3wYy1M0Cng"  # Substitua pelo token do seu bot

# Dicionário de Morse e inverso
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..',
    'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..',
    '9': '----.', '0': '-----',
    ',': '--..--', '.': '.-.-.-', '?': '..--..', '/': '-..-.',
    '-': '-....-', '(': '-.--.', ')': '-.--.-', ' ': '/'
}
REVERSE_MORSE_CODE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}

# Funções de decodificação
def binary_to_text(binary_str: str) -> str:
    try:
        words = binary_str.split()
        return ''.join(chr(int(b, 2)) for b in words)
    except Exception as e:
        return f"Erro: {e}"

def morse_to_text(morse_str: str) -> str:
    try:
        words = morse_str.split(" / ")
        decoded_words = []
        for word in words:
            letters = word.split()
            decoded_word = ''.join(REVERSE_MORSE_CODE_DICT.get(letter, '') for letter in letters)
            decoded_words.append(decoded_word)
        return ' '.join(decoded_words)
    except Exception as e:
        return f"Erro: {e}"

# Classe para gerenciar a reprodução de música
class MusicPlayer:
    def __init__(self, voice_client: discord.VoiceClient):
        self.voice_client = voice_client
        self.queue = []  # Cada item: dict com "title" e "url"
        self.loop = False
        self.volume = 1.0
        self.current = None

    def play_next(self):
        if self.queue:
            track = self.queue.pop(0)
            self.current = track
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    track["url"],
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                ),
                volume=self.volume
            )
            self.voice_client.play(source, after=lambda e: self.after_play(e))
        else:
            self.current = None

    def after_play(self, error):
        if error:
            print("Erro na reprodução:", error)
        if self.loop and self.current:
            self.queue.insert(0, self.current)
        self.play_next()

# Dicionário global para players de música (por guild)
music_players = {}

# Função de autocompletar para o parâmetro "quality"
async def quality_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    try:
        url = interaction.namespace.url
    except Exception:
        return []
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        choices = []
        for fmt in info.get("formats", []):
            quality_str = fmt.get("format")
            if quality_str and current.lower() in quality_str.lower():
                choices.append(app_commands.Choice(name=quality_str, value=quality_str))
            if len(choices) >= 10:
                break
        return choices
    except Exception:
        return []

# Função auxiliar para enviar mensagens de erro grandes como anexo
async def send_error(interaction: discord.Interaction, error_message: str):
    if len(error_message) > 1900:
        temp_error = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
        temp_error.write(error_message)
        temp_error.close()
        await interaction.followup.send("Erro ao baixar. Veja o arquivo anexo para mais detalhes.", file=discord.File(temp_error.name))
        os.remove(temp_error.name)
    else:
        await interaction.followup.send(f"Erro: ```{error_message}```")

# ─── BOT SETUP ─────────────────────────────────────────────
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.tree.add_command(download)
        self.tree.add_command(ocr)
        self.tree.add_command(bhaskara)
        self.tree.add_command(convert)
        self.tree.add_command(adjustaudio)
        self.tree.add_command(qrcode_command)
        self.tree.add_command(removebg)
        self.tree.add_command(fusion)
        self.tree.add_command(play)
        self.tree.add_command(pause)
        self.tree.add_command(resume)
        self.tree.add_command(skip)
        self.tree.add_command(queue)
        self.tree.add_command(lyrics)
        self.tree.add_command(volume_cmd)
        self.tree.add_command(loop_cmd)
        self.tree.add_command(translate_text)
        self.tree.add_command(decode)
        self.tree.add_command(help_command)
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

# ─── COMANDO /decode ─────────────────────────────────────────────
@app_commands.command(name="decode", description="Decodifica uma mensagem em binário ou morse para texto normal.")
@app_commands.describe(
    encoded_text="Mensagem codificada (binário ou morse)",
    mode="Modo: 'binary' para binário, 'morse' para morse"
)
@app_commands.choices(
    mode=[app_commands.Choice(name="binary", value="binary"), app_commands.Choice(name="morse", value="morse")]
)
async def decode(interaction: discord.Interaction, encoded_text: str, mode: app_commands.Choice[str]):
    await interaction.response.defer()
    if mode.value == "binary":
        decoded = binary_to_text(encoded_text)
    elif mode.value == "morse":
        decoded = morse_to_text(encoded_text)
    else:
        decoded = "Modo inválido."
    await interaction.followup.send(f"Mensagem decodificada:\n```{decoded}```")

# ─── COMANDO /download ─────────────────────────────────────────────
@app_commands.command(name="download", description="Baixa mídia e ajusta velocidade/legendas.")
@app_commands.describe(
    plataforma="Plataforma: youtube, instagram, soundcloud ou spotify",
    url="URL do conteúdo",
    file_format="Formato desejado (mp3, wav, mp4, webm)",
    quality="(Opcional) Qualidade desejada (ex.: '22' ou '137+140')",
    speed="(Opcional) Velocidade de reprodução (1 é normal)",
    subtitle="(Opcional) Código da legenda desejada (ex.: 'pt', 'en')"
)
@app_commands.choices(
    plataforma=[
        app_commands.Choice(name="youtube", value="youtube"),
        app_commands.Choice(name="instagram", value="instagram"),
        app_commands.Choice(name="soundcloud", value="soundcloud"),
        app_commands.Choice(name="spotify", value="spotify")
    ],
    file_format=[
        app_commands.Choice(name="mp3", value="mp3"),
        app_commands.Choice(name="wav", value="wav"),
        app_commands.Choice(name="mp4", value="mp4"),
        app_commands.Choice(name="webm", value="webm")
    ]
)
async def download(interaction: discord.Interaction, 
                   plataforma: app_commands.Choice[str], 
                   url: str, 
                   file_format: app_commands.Choice[str],
                   quality: str = None,
                   speed: float = 1.0,
                   subtitle: str = None):
    await interaction.response.defer()

    # Para Spotify, use spotdl com a palavra-chave "download"
    if plataforma.value == "spotify":
        if file_format.value != "mp3":
            await interaction.followup.send("O Spotify suporta apenas o formato mp3.")
            return
        await interaction.followup.send("Iniciando download de **Spotify** (mp3) usando spotdl...")
        temp_dir = tempfile.mkdtemp()
        try:
            command = ["spotdl", "download", url, "--format", "mp3", "--output", temp_dir]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                error_message = result.stderr.decode()
                await send_error(interaction, error_message)
                shutil.rmtree(temp_dir)
                return
            downloaded_files = os.listdir(temp_dir)
            if not downloaded_files:
                await interaction.followup.send("Nenhum arquivo foi baixado com spotdl.")
                shutil.rmtree(temp_dir)
                return
            file_path = os.path.join(temp_dir, downloaded_files[0])
            final_file = file_path
            if speed != 1.0:
                new_file = os.path.splitext(file_path)[0] + f"_speed.mp3"
                ffmpeg_cmd = ["ffmpeg", "-i", file_path, "-filter:a", f"atempo={speed}", "-vn", "-y", new_file]
                res = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode == 0:
                    os.remove(file_path)
                    final_file = new_file
                else:
                    await send_error(interaction, res.stderr.decode())
            if os.path.exists(final_file):
                await interaction.followup.send(file=discord.File(final_file))
            else:
                await interaction.followup.send("Arquivo não encontrado após o download.")
            shutil.rmtree(temp_dir)
        except Exception as e:
            await interaction.followup.send(f"Erro ao baixar com spotdl: {e}")
            shutil.rmtree(temp_dir)
        return

    # Para outras plataformas, usa yt_dlp
    await interaction.followup.send(f"Iniciando download de **{plataforma.value}** no formato **{file_format.value}**...")
    if file_format.value in ["mp3", "wav"]:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': file_format.value,
                'preferredquality': '192',
            }],
        }
    elif file_format.value in ["mp4", "webm"]:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s'
        }
    else:
        await interaction.followup.send("Formato inválido. Use mp3, wav, mp4 ou webm.")
        return
    if quality is not None:
        ydl_opts["format"] = quality
    if subtitle is not None:
        ydl_opts["writesubtitles"] = True
        ydl_opts["subtitleslangs"] = [subtitle]
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict)
            if file_format.value in ["mp3", "wav"]:
                file_name = os.path.splitext(file_name)[0] + f".{file_format.value}"
        final_file = file_name
        if speed != 1.0:
            new_file = os.path.splitext(file_name)[0] + f"_speed.{file_format.value}"
            if file_format.value in ["mp3", "wav"]:
                ffmpeg_cmd = ["ffmpeg", "-i", file_name, "-filter:a", f"atempo={speed}", "-vn", "-y", new_file]
            else:
                ffmpeg_cmd = ["ffmpeg", "-i", file_name, "-filter_complex", f"[0:v]setpts=PTS/{speed}[v];[0:a]atempo={speed}[a]", "-map", "[v]", "-map", "[a]", "-y", new_file]
            res = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0:
                os.remove(file_name)
                final_file = new_file
            else:
                await send_error(interaction, res.stderr.decode())
        if os.path.exists(final_file):
            await interaction.followup.send(file=discord.File(final_file))
        else:
            await interaction.followup.send("Arquivo não encontrado após o download.")
    except Exception as e:
        await interaction.followup.send(f"Erro ao baixar: {e}")

@download.autocomplete("quality")
async def quality_autocomplete_callback(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    try:
        url = interaction.namespace.url
    except Exception:
        return []
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        choices = []
        for fmt in info.get("formats", []):
            quality_str = fmt.get("format")
            if quality_str and current.lower() in quality_str.lower():
                choices.append(app_commands.Choice(name=quality_str, value=quality_str))
            if len(choices) >= 10:
                break
        return choices
    except Exception:
        return []

# ─── COMANDO /ocr ─────────────────────────────────────────────
@app_commands.command(name="ocr", description="Extrai texto de uma imagem a partir da URL ou de um anexo.")
@app_commands.describe(image_url="(Opcional) URL da imagem", attachment="(Opcional) Anexe uma imagem")
async def ocr(interaction: discord.Interaction, image_url: str = None, attachment: discord.Attachment = None):
    await interaction.response.defer()
    if attachment is not None:
        image_url = attachment.url
    if image_url is None:
        await interaction.followup.send("Por favor, forneça uma URL ou anexe uma imagem.")
        return
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Não foi possível baixar a imagem (verifique a URL).")
                    return
                data = await resp.read()
        except Exception as e:
            await interaction.followup.send(f"Erro ao baixar a imagem: {e}")
            return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp:
        temp.write(data)
        temp_path = temp.name
    try:
        image = Image.open(temp_path)
        texto_extraido = pytesseract.image_to_string(image, lang='por')
        await interaction.followup.send(f"Texto extraído:\n```{texto_extraido}```")
    except Exception as e:
        await interaction.followup.send(f"Erro ao processar a imagem: {e}")
    finally:
        os.remove(temp_path)

# ─── COMANDO /bhaskara ─────────────────────────────────────────────
@app_commands.command(name="bhaskara", description="Calcula as raízes de uma equação de segundo grau (Bhaskara).")
@app_commands.describe(a="Coeficiente de x²", b="Coeficiente de x", c="Termo constante", show_delta="Exibir delta?")
async def bhaskara(interaction: discord.Interaction, a: float, b: float, c: float, show_delta: bool = False):
    await interaction.response.defer()
    if a == 0:
        await interaction.followup.send("O coeficiente 'a' não pode ser zero em uma equação de segundo grau.")
        return
    delta = b**2 - 4 * a * c
    if delta < 0:
        sqrt_delta = math.sqrt(-delta)
        real_part = -b / (2 * a)
        imaginary_part = sqrt_delta / (2 * a)
        root1 = complex(real_part, imaginary_part)
        root2 = complex(real_part, -imaginary_part)
    else:
        sqrt_delta = math.sqrt(delta)
        root1 = (-b + sqrt_delta) / (2 * a)
        root2 = (-b - sqrt_delta) / (2 * a)
    response = f"Raízes da equação: `{root1}` e `{root2}`."
    if show_delta:
        response += f"\nDelta: `{delta}`"
    await interaction.followup.send(response)

# ─── COMANDO /convert ─────────────────────────────────────────────
@app_commands.command(name="convert", description="Converte um arquivo para o formato desejado e pode ajustar áudio.")
@app_commands.describe(
    target_format="Formato de destino (ex: mp3, wav, mp4, webm)",
    attachment="Anexe um arquivo (opcional, se não fornecer file_url)",
    file_url="URL do arquivo (opcional, se não fornecer um anexo)",
    audio_speed="(Opcional) Velocidade do áudio (1.0 é normal)",
    volume="(Opcional) Fator de volume (1.0 é o volume original)"
)
async def convert(interaction: discord.Interaction, target_format: str, attachment: discord.Attachment = None, file_url: str = None, audio_speed: float = 1.0, volume: float = 1.0):
    await interaction.response.defer()
    if file_url is None and attachment is None:
        await interaction.followup.send("Por favor, forneça uma URL ou anexe um arquivo para conversão.")
        return
    if attachment is not None:
        file_url = attachment.url
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(file_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Não foi possível baixar o arquivo (verifique a URL).")
                    return
                input_data = await resp.read()
        except Exception as e:
            await interaction.followup.send(f"Erro ao baixar o arquivo: {e}")
            return
    parsed_url = urlparse(file_url)
    input_ext = os.path.splitext(parsed_url.path)[1]
    if not input_ext:
        input_ext = ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=input_ext) as temp_in:
        temp_in.write(input_data)
        input_path = temp_in.name
    output_path = os.path.splitext(input_path)[0] + f".{target_format.lower()}"
    filter_args = []
    if audio_speed != 1.0:
        filter_args.append(f"atempo={audio_speed}")
    if volume != 1.0:
        filter_args.append(f"volume={volume}")
    if filter_args:
        filter_str = ",".join(filter_args)
        ffmpeg_cmd = ["ffmpeg", "-i", input_path, "-filter:a", filter_str, "-vn", "-y", output_path]
    else:
        ffmpeg_cmd = ["ffmpeg", "-i", input_path, "-y", output_path]
    try:
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            await send_error(interaction, result.stderr.decode())
            os.remove(input_path)
            return
    except Exception as e:
        await interaction.followup.send(f"Erro ao executar o ffmpeg: {e}")
        os.remove(input_path)
        return
    if os.path.exists(output_path):
        await interaction.followup.send(file=discord.File(output_path))
        os.remove(output_path)
    else:
        await interaction.followup.send("Falha ao encontrar o arquivo convertido.")
    os.remove(input_path)

# ─── COMANDO /adjustaudio ─────────────────────────────────────────────
@app_commands.command(name="adjustaudio", description="Ajusta a velocidade e o volume de um áudio/vídeo sem alterar seu formato.")
@app_commands.describe(
    attachment="Anexe um arquivo (opcional, se não fornecer file_url)",
    file_url="URL do arquivo (opcional, se não fornecer um anexo)",
    audio_speed="(Opcional) Velocidade do áudio (1.0 é normal)",
    volume="(Opcional) Fator de volume (1.0 é o padrão)"
)
async def adjustaudio(interaction: discord.Interaction, attachment: discord.Attachment = None, file_url: str = None, audio_speed: float = 1.0, volume: float = 1.0):
    await interaction.response.defer()
    if file_url is None and attachment is None:
        await interaction.followup.send("Por favor, forneça uma URL ou anexe um arquivo para ajuste.")
        return
    if attachment is not None:
        file_url = attachment.url
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(file_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Não foi possível baixar o arquivo (verifique a URL).")
                    return
                input_data = await resp.read()
        except Exception as e:
            await interaction.followup.send(f"Erro ao baixar o arquivo: {e}")
            return
    parsed_url = urlparse(file_url)
    input_ext = os.path.splitext(parsed_url.path)[1]
    if not input_ext:
        input_ext = ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=input_ext) as temp_in:
        temp_in.write(input_data)
        input_path = temp_in.name
    output_path = os.path.splitext(input_path)[0] + f"_adjusted{input_ext}"
    filter_args = []
    if audio_speed != 1.0:
        filter_args.append(f"atempo={audio_speed}")
    if volume != 1.0:
        filter_args.append(f"volume={volume}")
    if filter_args:
        filter_str = ",".join(filter_args)
        ffmpeg_cmd = ["ffmpeg", "-i", input_path, "-filter:a", filter_str, "-vn", "-y", output_path]
    else:
        ffmpeg_cmd = ["ffmpeg", "-i", input_path, "-y", output_path]
    try:
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            await send_error(interaction, result.stderr.decode())
            os.remove(input_path)
            return
    except Exception as e:
        await interaction.followup.send(f"Erro ao executar o ffmpeg: {e}")
        os.remove(input_path)
        return
    if os.path.exists(output_path):
        await interaction.followup.send(file=discord.File(output_path))
        os.remove(output_path)
    else:
        await interaction.followup.send("Falha ao encontrar o arquivo ajustado.")
    os.remove(input_path)

# ─── COMANDO /qrcode ─────────────────────────────────────────────
@app_commands.command(name="qrcode", description="Gera um QR Code a partir de um texto ou URL.")
@app_commands.describe(text="Texto ou URL para gerar o QR Code")
async def qrcode_command(interaction: discord.Interaction, text: str):
    await interaction.response.defer()
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img.save(temp_file.name)
        temp_file.close()
        await interaction.followup.send(file=discord.File(temp_file.name))
        os.remove(temp_file.name)
    except Exception as e:
        await interaction.followup.send(f"Erro ao gerar o QR Code: {e}")

# ─── COMANDO /removebg ─────────────────────────────────────────────
@app_commands.command(name="removebg", description="Remove o fundo de uma imagem.")
@app_commands.describe(file_url="URL da imagem (se não informado, use um anexo)")
async def removebg(interaction: discord.Interaction, file_url: str = None):
    await interaction.response.defer()
    if file_url is None:
        if interaction.data.get("attachments"):
            file_url = interaction.data["attachments"][0]["url"]
        else:
            await interaction.followup.send("Por favor, forneça uma URL ou anexe uma imagem.")
            return
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(file_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Não foi possível baixar a imagem (verifique a URL).")
                    return
                input_data = await resp.read()
        except Exception as e:
            await interaction.followup.send(f"Erro ao baixar a imagem: {e}")
            return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_in:
        temp_in.write(input_data)
        input_path = temp_in.name
    output_path = os.path.splitext(input_path)[0] + "_no_bg.png"
    try:
        with open(input_path, 'rb') as i:
            input_bytes = i.read()
        output_bytes = remove_bg(input_bytes)
        with open(output_path, 'wb') as o:
            o.write(output_bytes)
        if os.path.exists(output_path):
            await interaction.followup.send(file=discord.File(output_path))
            os.remove(output_path)
        else:
            await interaction.followup.send("Falha ao encontrar a imagem processada.")
    except Exception as e:
        await interaction.followup.send(f"Erro ao remover o fundo: {e}")
    finally:
        os.remove(input_path)

# ─── COMANDO /fusion ─────────────────────────────────────────────
@app_commands.command(name="fusion", description="Funde duas imagens horizontalmente.")
@app_commands.describe(
    image1="Primeira imagem (anexe um arquivo)",
    image2="Segunda imagem (anexe um arquivo)"
)
async def fusion(interaction: discord.Interaction, image1: discord.Attachment, image2: discord.Attachment):
    await interaction.response.defer()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image1.url) as resp1:
                if resp1.status != 200:
                    await interaction.followup.send("Não foi possível baixar a primeira imagem.")
                    return
                data1 = await resp1.read()
            async with session.get(image2.url) as resp2:
                if resp2.status != 200:
                    await interaction.followup.send("Não foi possível baixar a segunda imagem.")
                    return
                data2 = await resp2.read()
        img1 = Image.open(BytesIO(data1)).convert("RGBA")
        img2 = Image.open(BytesIO(data2)).convert("RGBA")
        new_height = min(img1.height, img2.height)
        img1 = img1.resize((int(img1.width * new_height / img1.height), new_height))
        img2 = img2.resize((int(img2.width * new_height / img2.height), new_height))
        new_width = img1.width + img2.width
        fusion_img = Image.new("RGBA", (new_width, new_height))
        fusion_img.paste(img1, (0, 0))
        fusion_img.paste(img2, (img1.width, 0))
        fusion_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fusion_img.save(fusion_file.name)
        fusion_file.close()
        await interaction.followup.send(file=discord.File(fusion_file.name))
        os.remove(fusion_file.name)
    except Exception as e:
        await interaction.followup.send(f"Erro ao fundir imagens: {e}")

# ─── COMANDO /play ─────────────────────────────────────────────
@app_commands.command(name="play", description="Reproduz uma música do YouTube, SoundCloud ou Spotify.")
@app_commands.describe(query="URL ou nome da música")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("Você precisa estar em um canal de voz para usar este comando.")
        return
    channel = interaction.user.voice.channel
    guild_id = interaction.guild.id
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        try:
            voice_client = await channel.connect()
        except Exception as e:
            await interaction.followup.send(f"Erro ao entrar no canal de voz: {e}")
            return
    if guild_id not in music_players:
        music_players[guild_id] = MusicPlayer(voice_client)
    player = music_players[guild_id]
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'quiet': True
    }
    try:
        if "open.spotify.com" in query.lower():
            temp_dir = tempfile.mkdtemp()
            command = ["spotdl", "download", query, "--format", "mp3", "--output", temp_dir]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                error_message = result.stderr.decode()
                await send_error(interaction, error_message)
                shutil.rmtree(temp_dir)
                return
            downloaded_files = os.listdir(temp_dir)
            if not downloaded_files:
                await interaction.followup.send("Nenhum arquivo foi baixado com spotdl.")
                shutil.rmtree(temp_dir)
                return
            file_path = os.path.join(temp_dir, downloaded_files[0])
            track = {"title": os.path.splitext(downloaded_files[0])[0], "url": file_path}
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if "entries" in info:
                    info = info["entries"][0]
            temp_dir = tempfile.mkdtemp()
            download_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'quiet': True
            }
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.download([info['webpage_url']])
            downloaded_files = os.listdir(temp_dir)
            if not downloaded_files:
                await interaction.followup.send("Nenhum arquivo foi baixado.")
                shutil.rmtree(temp_dir)
                return
            file_path = os.path.join(temp_dir, downloaded_files[0])
            track = {"title": info.get("title", "Unknown"), "url": file_path}
        player.queue.append(track)
        await interaction.followup.send(f"Adicionado à fila: **{track['title']}**")
        if not voice_client.is_playing():
            player.play_next()
    except Exception as e:
        await interaction.followup.send(f"Erro ao reproduzir a música: {e}")

# ─── COMANDO /pause ─────────────────────────────────────────────
@app_commands.command(name="pause", description="Pausa a música atual.")
async def pause(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.followup.send("Música pausada.")
    else:
        await interaction.followup.send("Nenhuma música está sendo reproduzida.")

# ─── COMANDO /resume ─────────────────────────────────────────────
@app_commands.command(name="resume", description="Retoma a música pausada.")
async def resume(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.followup.send("Música retomada.")
    else:
        await interaction.followup.send("Nenhuma música está pausada.")

# ─── COMANDO /skip ─────────────────────────────────────────────
@app_commands.command(name="skip", description="Pula para a próxima música na fila.")
async def skip(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.followup.send("Música pulada.")
    else:
        await interaction.followup.send("Nenhuma música está sendo reproduzida.")

# ─── COMANDO /queue ─────────────────────────────────────────────
@app_commands.command(name="queue", description="Mostra a lista de músicas na fila.")
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    if guild_id in music_players:
        player = music_players[guild_id]
        if player.queue:
            queue_list = "\n".join([f"{i+1}. {track['title']}" for i, track in enumerate(player.queue)])
            await interaction.followup.send(f"**Fila de Música:**\n{queue_list}")
        else:
            await interaction.followup.send("A fila está vazia.")
    else:
        await interaction.followup.send("Nenhuma música foi adicionada.")

# ─── COMANDO /lyrics ─────────────────────────────────────────────
@app_commands.command(name="lyrics", description="Busca a letra da música.")
@app_commands.describe(song="Nome da música ou URL")
async def lyrics(interaction: discord.Interaction, song: str):
    await interaction.response.defer()
    await interaction.followup.send(f"Letra da música '{song}':\n[Letra não implementada]")

# ─── COMANDO /volume ─────────────────────────────────────────────
@app_commands.command(name="volume", description="Ajusta o volume da música (1-100).")
@app_commands.describe(volume="Volume desejado (1 a 100)")
async def volume_cmd(interaction: discord.Interaction, volume: int):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    if guild_id in music_players:
        player = music_players[guild_id]
        player.volume = volume / 100.0
        if player.voice_client.source:
            player.voice_client.source.volume = player.volume
        await interaction.followup.send(f"Volume ajustado para {volume}%.")
    else:
        await interaction.followup.send("Nenhuma música está sendo reproduzida.")

# ─── COMANDO /loop ─────────────────────────────────────────────
@app_commands.command(name="loop", description="Ativa ou desativa o loop da música atual.")
async def loop_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    if guild_id in music_players:
        player = music_players[guild_id]
        player.loop = not player.loop
        status = "ativado" if player.loop else "desativado"
        await interaction.followup.send(f"Loop {status}.")
    else:
        await interaction.followup.send("Nenhuma música está sendo reproduzida.")

# ─── COMANDO /translate ─────────────────────────────────────────────
@app_commands.command(name="translate", description="Converte uma mensagem para binário ou morse.")
@app_commands.describe(
    text="Texto a ser convertido",
    mode="Modo: 'binary' para binário, 'morse' para morse"
)
@app_commands.choices(
    mode=[app_commands.Choice(name="binary", value="binary"), app_commands.Choice(name="morse", value="morse")]
)
async def translate_text(interaction: discord.Interaction, text: str, mode: app_commands.Choice[str]):
    await interaction.response.defer()
    if mode.value == "binary":
        result = ' '.join(format(ord(c), '08b') for c in text)
    elif mode.value == "morse":
        result = ' '.join(MORSE_CODE_DICT.get(char.upper(), '') for char in text)
    else:
        result = "Modo inválido."
    await interaction.followup.send(f"Resultado:\n```{result}```")

# ─── COMANDO /decode ─────────────────────────────────────────────
@app_commands.command(name="decode", description="Decodifica uma mensagem em binário ou morse para texto normal.")
@app_commands.describe(
    encoded_text="Mensagem codificada (binário ou morse)",
    mode="Modo: 'binary' para decodificar binário, 'morse' para decodificar morse"
)
@app_commands.choices(
    mode=[app_commands.Choice(name="binary", value="binary"), app_commands.Choice(name="morse", value="morse")]
)
async def decode(interaction: discord.Interaction, encoded_text: str, mode: app_commands.Choice[str]):
    await interaction.response.defer()
    if mode.value == "binary":
        decoded = binary_to_text(encoded_text)
    elif mode.value == "morse":
        decoded = morse_to_text(encoded_text)
    else:
        decoded = "Modo inválido."
    await interaction.followup.send(f"Mensagem decodificada:\n```{decoded}```")

# ─── COMANDO /fusion ─────────────────────────────────────────────
@app_commands.command(name="fusion", description="Funde duas imagens horizontalmente.")
@app_commands.describe(
    image1="Primeira imagem (anexe um arquivo)",
    image2="Segunda imagem (anexe um arquivo)"
)
async def fusion(interaction: discord.Interaction, image1: discord.Attachment, image2: discord.Attachment):
    await interaction.response.defer()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image1.url) as resp1:
                if resp1.status != 200:
                    await interaction.followup.send("Não foi possível baixar a primeira imagem.")
                    return
                data1 = await resp1.read()
            async with session.get(image2.url) as resp2:
                if resp2.status != 200:
                    await interaction.followup.send("Não foi possível baixar a segunda imagem.")
                    return
                data2 = await resp2.read()
        img1 = Image.open(BytesIO(data1)).convert("RGBA")
        img2 = Image.open(BytesIO(data2)).convert("RGBA")
        new_height = min(img1.height, img2.height)
        img1 = img1.resize((int(img1.width * new_height / img1.height), new_height))
        img2 = img2.resize((int(img2.width * new_height / img2.height), new_height))
        new_width = img1.width + img2.width
        fusion_img = Image.new("RGBA", (new_width, new_height))
        fusion_img.paste(img1, (0, 0))
        fusion_img.paste(img2, (img1.width, 0))
        fusion_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fusion_img.save(fusion_file.name)
        fusion_file.close()
        await interaction.followup.send(file=discord.File(fusion_file.name))
        os.remove(fusion_file.name)
    except Exception as e:
        await interaction.followup.send(f"Erro ao fundir imagens: {e}")

# ─── COMANDO /help ─────────────────────────────────────────────
@app_commands.command(name="help", description="Exibe a lista de comandos disponíveis.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Comandos do Bot", color=discord.Color.blue())
    embed.add_field(
        name="/download",
        value=(
            "Baixa mídia e ajusta qualidade, velocidade e legendas.\n"
            "Parâmetros: plataforma, url, file_format, quality (opcional), speed (opcional), subtitle (opcional)."
        ),
        inline=False
    )
    embed.add_field(
        name="/ocr",
        value="Extrai texto de uma imagem. Parâmetros: image_url ou attachment.",
        inline=False
    )
    embed.add_field(
        name="/bhaskara",
        value="Calcula as raízes de uma equação de segundo grau.\nParâmetros: a, b, c, show_delta (opcional).",
        inline=False
    )
    embed.add_field(
        name="/convert",
        value="Converte um arquivo para o formato desejado e ajusta áudio.\nParâmetros: target_format, attachment ou file_url, audio_speed, volume.",
        inline=False
    )
    embed.add_field(
        name="/adjustaudio",
        value="Ajusta velocidade e volume de um áudio/vídeo sem alterar seu formato.\nParâmetros: attachment ou file_url, audio_speed, volume.",
        inline=False
    )
    embed.add_field(
        name="/fusion",
        value="Funde duas imagens horizontalmente. Parâmetros: image1, image2.",
        inline=False
    )
    embed.add_field(
        name="/play",
        value="Reproduz uma música do YouTube, SoundCloud ou Spotify.\nParâmetro: query (URL ou nome).",
        inline=False
    )
    embed.add_field(
        name="/pause",
        value="Pausa a música atual.",
        inline=False
    )
    embed.add_field(
        name="/resume",
        value="Retoma a música pausada.",
        inline=False
    )
    embed.add_field(
        name="/skip",
        value="Pula para a próxima música na fila.",
        inline=False
    )
    embed.add_field(
        name="/queue",
        value="Mostra a lista de músicas na fila.",
        inline=False
    )
    embed.add_field(
        name="/lyrics",
        value="Busca a letra da música.\nParâmetro: song.",
        inline=False
    )
    embed.add_field(
        name="/volume",
        value="Ajusta o volume da música (1-100).",
        inline=False
    )
    embed.add_field(
        name="/loop",
        value="Ativa ou desativa o loop da música atual.",
        inline=False
    )
    embed.add_field(
        name="/translate",
        value="Converte uma mensagem para binário ou morse.\nParâmetros: text, mode.",
        inline=False
    )
    embed.add_field(
        name="/decode",
        value="Decodifica uma mensagem em binário ou morse para texto normal.\nParâmetros: encoded_text, mode.",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
