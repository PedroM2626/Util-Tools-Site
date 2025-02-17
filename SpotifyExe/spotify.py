import os
from spotdl import Spotdl
from spotdl.types.options import SpotDLOptions

# Definir as credenciais do Spotify
SPOTIFY_CLIENT_ID = "dfaf0094de38454684f6dc0a9dfc3128"
SPOTIFY_CLIENT_SECRET = "89bc0789204f4cd0a84557958b18dda1"

def baixar_musica(link_spotify):
    try:
        # Cria as opções padrão e desativa a incorporação de metadados
        spotdl_options = SpotDLOptions()
        spotdl_options["no_metadata"] = True  # Desabilita embedding de metadados
        
        # Inicializa o Spotdl com as credenciais
        spotdl_instance = Spotdl(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
        spotdl_instance.options = spotdl_options

        # Buscar a música
        print(f"Baixando música: {link_spotify}")
        songs = spotdl_instance.search([link_spotify])  # Retorna uma lista
        if not songs:
            print("Música não encontrada. Verifique o link.")
            return
        song = songs[0]  # Pega a primeira música da lista

        # Baixar a música (a opção no_metadata já desativa a etapa de embedding de metadados)
        spotdl_instance.download(song)
        print(f"Música baixada com sucesso: {song.display_name}")
    except Exception as e:
        print(f"Erro ao baixar a música: {e}")

def validar_link(link):
    """
    Verifica se o link é válido para uma música do Spotify.
    """
    link = link.strip()
    return ("open.spotify.com/track" in link or 
            "spotify.link" in link or 
            "open.spotify.com/intl-pt/track/" in link)

def main():
    while True:
        print("Bem-vindo ao Sistema de Download de Músicas do Spotify!")
        link_spotify = input("Cole o link da música do Spotify aqui (ou digite 'sair' para encerrar): ")

        if link_spotify.lower() == "sair":
            print("Encerrando o programa...")
            break

        if validar_link(link_spotify):
            baixar_musica(link_spotify)
        else:
            print("Link inválido. Certifique-se de que é um link de música do Spotify.")

if __name__ == "__main__":
    main()