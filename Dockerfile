# Use uma imagem base Python (por exemplo, Python 3.12)
FROM python:3.12-slim

# Instale dependências do sistema, incluindo Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos do projeto para o container
COPY . /app

# Instale as dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Exponha a porta em que o Flask vai rodar
EXPOSE 8080

# Comando para iniciar o servidor (ajuste conforme necessário)
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
