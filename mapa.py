from flask import Flask, render_template, request, jsonify
import requests
from geopy.distance import geodesic
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

# Função para buscar CEP com um raio específico
def buscar_cep_com_raio(lat, lon, raio=0):
    if raio == 0:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
    else:
        url = f"https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=1" + \
              f"&viewbox={lon-raio},{lat-raio},{lon+raio},{lat+raio}"
    
    try:
        response = requests.get(url, headers={"User-Agent": "DistanceCalculator/1.0"})
        data = response.json()
        address = None
        
        if isinstance(data, list) and data:
            if 'address' in data[0]:
                address = data[0]['address']
        elif isinstance(data, dict):
            if 'address' in data:
                address = data['address']
        
        if address:
            if 'postcode' in address:
                return address['postcode']
            
            for campo in ['postalcode', 'postal_code', 'zip', 'zipcode']:
                if campo in address and address[campo]:
                    return address[campo]
        
        return None
        
    except Exception as e:
        print(f"Erro ao buscar CEP: {str(e)}")
        return None

# Função para buscar CEP da cidade
def buscar_cep_da_cidade(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1&zoom=10"
    
    try:
        response = requests.get(url, headers={"User-Agent": "DistanceCalculator/1.0"})
        data = response.json()
        
        if 'address' in data:
            address = data['address']
            
            if 'postcode' in address:
                return address['postcode']
            
            if 'city' in address or 'town' in address or 'municipality' in address:
                cidade = address.get('city', address.get('town', address.get('municipality', '')))
                if cidade:
                    busca_url = f"https://nominatim.openstreetmap.org/search?format=json&city={cidade}&country=Brazil&addressdetails=1&limit=1"
                    busca_resp = requests.get(busca_url, headers={"User-Agent": "DistanceCalculator/1.0"})
                    busca_data = busca_resp.json()
                    
                    if busca_data and len(busca_data) > 0 and 'address' in busca_data[0] and 'postcode' in busca_data[0]['address']:
                        return busca_data[0]['address']['postcode']
        
        return None
        
    except Exception as e:
        print(f"Erro ao buscar CEP da cidade: {str(e)}")
        return None

# Função para obter CEP a partir de coordenadas
def obter_cep(lat, lon):
    try:
        # Tentar obter o CEP a partir do ponto exato
        resultado = buscar_cep_com_raio(lat, lon, 0)
        
        if resultado:
            return {"cep": resultado, "tipo": "exato"}
        
        # Se não encontrou, tentar gradualmente com raios maiores
        for raio in [0.001, 0.005, 0.01, 0.05, 0.1]:
            resultado = buscar_cep_com_raio(lat, lon, raio)
            if resultado:
                return {"cep": resultado, "tipo": "aproximado"}
        
        # Se ainda não encontrou, tentar obter CEP da cidade/região
        resultado = buscar_cep_da_cidade(lat, lon)
        if resultado:
            return {"cep": resultado, "tipo": "cidade"}
        
        return {"cep": "Não encontrado", "tipo": "nenhum"}
    except Exception as e:
        print(f"Erro em obter_cep({lat}, {lon}): {str(e)}")
        return {"cep": "Erro", "tipo": "erro"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calcular', methods=['POST'])
def calcular():
    try:
        # Verificar se há dados JSON na requisição
        if not request.is_json:
            print("Erro: Requisição não contém JSON")
            return jsonify({'error': 'Requisição deve ser JSON'}), 400
        
        data = request.json
        
        # Validar dados de entrada
        if 'ponto1' not in data or 'ponto2' not in data:
            print("Erro: Dados incompletos - faltam pontos")
            return jsonify({'error': 'Dados incompletos. Pontos 1 e 2 são necessários'}), 400
            
        if 'lat' not in data['ponto1'] or 'lng' not in data['ponto1'] or 'lat' not in data['ponto2'] or 'lng' not in data['ponto2']:
            print("Erro: Dados mal formatados - faltam coordenadas")
            return jsonify({'error': 'Formato inválido. Coordenadas lat/lng são necessárias'}), 400
        
        # Extrair coordenadas
        ponto1 = (float(data['ponto1']['lat']), float(data['ponto1']['lng']))
        ponto2 = (float(data['ponto2']['lat']), float(data['ponto2']['lng']))
        
        print(f"Calculando distância entre: {ponto1} e {ponto2}")
        
        # Calcular distância
        distancia = geodesic(ponto1, ponto2).kilometers
        
        # Obter CEPs com tratamento de erro
        try:
            cep1 = obter_cep(ponto1[0], ponto1[1])
        except Exception as e:
            print(f"Erro ao obter CEP1: {str(e)}")
            cep1 = {"cep": "Erro ao obter CEP", "tipo": "erro"}
            
        try:
            cep2 = obter_cep(ponto2[0], ponto2[1])
        except Exception as e:
            print(f"Erro ao obter CEP2: {str(e)}")
            cep2 = {"cep": "Erro ao obter CEP", "tipo": "erro"}
        
        # Montar resposta
        resposta = {
            'distancia': round(distancia, 2),
            'cep1': cep1,
            'cep2': cep2
        }
        
        print(f"Resposta calculada: {resposta}")
        return jsonify(resposta)
        
    except Exception as e:
        print(f"Erro na rota /api/calcular: {str(e)}")
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500

if __name__ == '__main__':
    # Criar diretórios se não existirem
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True)
