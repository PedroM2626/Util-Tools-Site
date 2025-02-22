# Use uma imagem base Python adequada
FROM python:3.12-slim

# Instale as dependências do sistema, incluindo Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev && \
    rm -rf /var/lib/apt/lists/*


# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos do projeto para o container
COPY . /app

# Instale as dependências Python (certifique-se de ter um requirements.txt)
RUN pip install --upgrade pip && pip install -r requirements.txt

# Exponha a porta que seu app utiliza (ex.: 8080)
EXPOSE 8080

# Comando para iniciar o servidor (ajuste conforme necessário)
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
