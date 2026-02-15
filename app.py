from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import re
from urllib.parse import quote_plus

app = Flask(__name__)
CORS(app)

class CNPJScraper:
    def __init__(self, delay=3):
        self.delay = delay
        self.ua = UserAgent()
        self.session = requests.Session()
        
    def get_headers(self, referer=None):
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        if referer:
            headers['Referer'] = referer
        return headers
    
    def buscar_google(self, bairro, cnae, max_results=20):
    query = f'"Bairro: {bairro}" "{cnae}" site:cnpj.biz'
    url = f'https://www.google.com/search?q={quote_plus(query)}&num={max_results}'
    
    print(f"🔍 Buscando: {query}")
    print(f"🌐 URL: {url}")
    
    try:
        response = self.session.get(url, headers=self.get_headers(), timeout=30)
        response.raise_for_status()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📄 Primeiros 500 caracteres da resposta:")
        print(response.text[:500])
        print("=" * 80)
        
        urls = re.findall(r'https?://cnpj\.biz/(\d{14})', response.text)
        urls_unicas = list(set(urls))
        
        print(f"📊 CNPJs encontrados: {len(urls_unicas)}")
        print(f"📋 Lista: {urls_unicas}")
        
        return urls_unicas
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return []
    
    def extrair_dados(self, html, cnpj):
        soup = BeautifulSoup(html, 'html.parser')
        
        dados = {
            'cnpj': cnpj,
            'url': f'https://cnpj.biz/{cnpj}',
            'razao_social': '',
            'nome_fantasia': '',
            'cnae_principal': '',
            'bairro': '',
            'municipio': '',
            'uf': '',
            'telefone': '',
            'email': '',
        }
        
        # Extrair dados de tabelas
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if 'razão social' in label or 'razao social' in label:
                        dados['razao_social'] = value
                    elif 'nome fantasia' in label:
                        dados['nome_fantasia'] = value
                    elif 'cnae principal' in label:
                        dados['cnae_principal'] = value
                    elif 'bairro' in label:
                        dados['bairro'] = value
                    elif 'município' in label or 'municipio' in label:
                        dados['municipio'] = value
                    elif 'uf' in label:
                        dados['uf'] = value
                    elif 'telefone' in label:
                        dados['telefone'] = value
                    elif 'email' in label or 'e-mail' in label:
                        dados['email'] = value
        
        return dados
    
    def buscar_cnpj(self, cnpj):
        url = f'https://cnpj.biz/{cnpj}'
        
        try:
            response = self.session.get(
                url,
                headers=self.get_headers(referer='https://www.google.com/'),
                timeout=30
            )
            response.raise_for_status()
            dados = self.extrair_dados(response.text, cnpj)
            return dados if dados['razao_social'] else None
        except:
            return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'CNPJ Scraper API está funcionando!'})

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.json
        bairro = data.get('bairro')
        cnae = data.get('cnae')
        max_results = data.get('max', 20)
        delay = data.get('delay', 3)
        
        if not bairro or not cnae:
            return jsonify({
                'success': False,
                'error': 'Parâmetros bairro e cnae são obrigatórios'
            }), 400
        
        scraper = CNPJScraper(delay=delay)
        
        # Buscar CNPJs no Google
        cnpjs = scraper.buscar_google(bairro, cnae, max_results)
        
        if not cnpjs:
            return jsonify({
                'success': True,
                'total': 0,
                'data': [],
                'message': 'Nenhum CNPJ encontrado'
            })
        
        # Processar cada CNPJ
        resultados = []
        for cnpj in cnpjs:
            dados = scraper.buscar_cnpj(cnpj)
            if dados:
                resultados.append(dados)
            time.sleep(delay)
        
        return jsonify({
            'success': True,
            'total': len(resultados),
            'data': resultados
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
