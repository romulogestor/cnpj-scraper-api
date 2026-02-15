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
