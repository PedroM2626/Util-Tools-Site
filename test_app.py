import unittest
import os
import tempfile
import io
from unittest.mock import patch, MagicMock
from app import app
from PIL import Image

class UtilToolsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        # Criar diretório de uploads temporário para testes
        app.config['TESTING'] = True
        self.temp_dir = tempfile.TemporaryDirectory()
        app.config['UPLOAD_FOLDER'] = self.temp_dir.name

    def tearDown(self):
        self.app_context.pop()
        self.temp_dir.cleanup()

    def test_index_page(self):
        """Testa se a página inicial carrega corretamente"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Util Tools', response.data)

    def test_sobre_page(self):
        """Testa se a página sobre carrega corretamente"""
        response = self.app.get('/sobre')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sobre', response.data)

    def test_ytc_page(self):
        """Testa se a página do YouTube Converter carrega corretamente"""
        response = self.app.get('/ytc')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'YouTube Converter', response.data)

    def test_mdcr_page(self):
        """Testa se a página do Music Downloader carrega corretamente"""
        response = self.app.get('/mdcr')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Music Downloader', response.data)

    def test_inscon_page(self):
        """Testa se a página do Instagram Content Downloader carrega corretamente"""
        response = self.app.get('/inscon')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Instagram Content Downloader', response.data)

    def test_imagermbg_page(self):
        """Testa se a página de remoção de fundo carrega corretamente"""
        response = self.app.get('/imagermbg')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Remover Fundo de Imagem', response.data)

    def test_ocr_page(self):
        """Testa se a página de OCR carrega corretamente"""
        response = self.app.get('/ocr')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'OCR', response.data)

    def test_mptmp_page(self):
        """Testa se a página de conversão MP4 para MP3 carrega corretamente"""
        response = self.app.get('/mptmp')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MP4 para MP3', response.data)

    def test_ocr_upload_without_file(self):
        """Testa o comportamento do OCR quando nenhum arquivo é enviado"""
        response = self.app.post('/ocr', data={})
        self.assertEqual(response.status_code, 200)  # Retorna a página com mensagem
        self.assertIn(b'Nenhum arquivo selecionado', response.data)

    def test_mptmp_upload_without_file(self):
        """Testa o comportamento do conversor MP4 para MP3 quando nenhum arquivo é enviado"""
        response = self.app.post('/mptmp', data={})
        self.assertEqual(response.status_code, 200)  # Retorna a página com mensagem
        self.assertIn(b'Nenhum arquivo selecionado', response.data)

    def test_imagermbg_upload_without_file(self):
        """Testa o comportamento do removedor de fundo quando nenhum arquivo é enviado"""
        response = self.app.post('/imagermbg', data={})
        self.assertEqual(response.status_code, 200)  # Retorna a página com mensagem
        self.assertIn(b'Nenhum arquivo selecionado', response.data)

    def test_ytc_empty_url(self):
        """Testa o comportamento do YouTube Converter com URL vazia"""
        response = self.app.post('/ytc', data={'url': '', 'formato': 'mp4', 'qualidade': 'best'})
        self.assertEqual(response.status_code, 200)
        # Deve retornar a página com uma mensagem de erro
        self.assertIn(b'Por favor, insira uma URL v', response.data)

    def test_ytc_invalid_url(self):
        """Testa o comportamento do YouTube Converter com URL inválida"""
        response = self.app.post('/ytc', data={'url': 'invalid_url', 'formato': 'mp4', 'qualidade': 'best'})
        self.assertEqual(response.status_code, 200)
        # Deve retornar a página com uma mensagem de erro
        self.assertIn(b'Erro', response.data)

    def test_mdcr_empty_url(self):
        """Testa o comportamento do Music Downloader com URL vazia"""
        response = self.app.post('/mdcr', data={'url': ''})
        self.assertEqual(response.status_code, 200)
        # Deve retornar a página com uma mensagem de erro
        self.assertIn(b'Por favor, insira uma URL v', response.data)

    def test_mdcr_invalid_url(self):
        """Testa o comportamento do Music Downloader com URL inválida"""
        response = self.app.post('/mdcr', data={'url': 'invalid_url'})
        self.assertEqual(response.status_code, 200)
        # Deve retornar a página com uma mensagem de erro
        self.assertIn(b'Erro', response.data)

    def test_inscon_empty_url(self):
        """Testa o comportamento do Instagram Content Downloader com URL vazia"""
        response = self.app.post('/inscon', data={'url': ''})
        self.assertEqual(response.status_code, 200)
        # Deve retornar a página com uma mensagem de erro
        self.assertIn(b'Por favor, insira uma URL v', response.data)

    def test_inscon_invalid_url(self):
        """Testa o comportamento do Instagram Content Downloader com URL inválida"""
        response = self.app.post('/inscon', data={'url': 'invalid_url'})
        self.assertEqual(response.status_code, 200)
        # Deve retornar a página com uma mensagem de erro
        self.assertIn(b'Erro', response.data)
        
    def test_ytc_upload_with_different_formats(self):
        """Testa o YouTube Converter com diferentes formatos"""
        formats = ['mp3', 'mp4', 'webm']
        for formato in formats:
            response = self.app.post('/ytc', data={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'formato': formato})
            self.assertEqual(response.status_code, 200)
    
    @patch('app.rembg_remove')
    def test_imagermbg_with_invalid_file_format(self, mock_rembg):
        """Testa o removedor de fundo com formato de arquivo inválido"""
        data = {'imagem': (io.BytesIO(b'invalid file content'), 'test.txt')}
        response = self.app.post('/imagermbg', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Formato de arquivo', response.data)
        mock_rembg.assert_not_called()
        
    @patch('app.rembg_remove')
    def test_imagermbg_functionality(self, mock_rembg):
        """Testa a funcionalidade de remoção de fundo"""
        # Criar uma imagem de teste
        test_image = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        test_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        # Configurar o mock para retornar uma imagem processada
        processed_image = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        mock_rembg.return_value = processed_image
        
        # Enviar a imagem para processamento
        data = {'imagem': (img_io, 'test.png')}
        response = self.app.post('/imagermbg', data=data, content_type='multipart/form-data')
        
        # Verificar se o processamento foi bem-sucedido
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Fundo removido com sucesso', response.data)
        mock_rembg.assert_called_once()
    
    @patch('app.pytesseract.image_to_string')
    def test_ocr_with_invalid_file_format(self, mock_ocr):
        """Testa o OCR com formato de arquivo inválido"""
        data = {'imagem': (io.BytesIO(b'invalid file content'), 'test.txt')}
        response = self.app.post('/ocr', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Formato de arquivo n', response.data)
        mock_ocr.assert_not_called()
    
    @patch('app.YoutubeDL')
    def test_ytc_network_error(self, mock_ydl):
        """Testa o YouTube Converter com erro de rede"""
        mock_instance = MagicMock()
        mock_instance.extract_info.side_effect = Exception("urlopen error")
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        response = self.app.post('/ytc', data={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'formato': 'mp3'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Erro de conex', response.data)

if __name__ == '__main__':
    unittest.main()
