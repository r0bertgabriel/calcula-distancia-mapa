document.addEventListener('DOMContentLoaded', function() {
    // Inicializar o mapa
    var map = L.map('map').setView([-15.77972, -47.92972], 4); // Centro no Brasil
    
    // Adicionar camada de mapa
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Variáveis para armazenar pontos
    var ponto1 = null;
    var ponto2 = null;
    var marker1 = null;
    var marker2 = null;
    var linha = null;
    
    // Manipular cliques no mapa
    map.on('click', function(e) {
        var lat = e.latlng.lat;
        var lng = e.latlng.lng;
        
        // Primeiro clique: ponto de origem
        if (ponto1 === null) {
            ponto1 = {lat: lat, lng: lng};
            document.getElementById('ponto1-coords').textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
            
            // Adicionar marcador
            marker1 = L.marker([lat, lng]).addTo(map);
            marker1.bindPopup("Origem").openPopup();
        } 
        // Segundo clique: ponto de destino
        else if (ponto2 === null) {
            ponto2 = {lat: lat, lng: lng};
            document.getElementById('ponto2-coords').textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
            
            // Adicionar marcador
            marker2 = L.marker([lat, lng]).addTo(map);
            marker2.bindPopup("Destino").openPopup();
            
            // Desenhar linha entre os pontos
            linha = L.polyline([
                [ponto1.lat, ponto1.lng],
                [ponto2.lat, ponto2.lng]
            ], {color: 'red'}).addTo(map);
        }
    });
    
    // Botão Resetar
    document.getElementById('btn-resetar').addEventListener('click', function() {
        // Remover marcadores e linha
        if (marker1) map.removeLayer(marker1);
        if (marker2) map.removeLayer(marker2);
        if (linha) map.removeLayer(linha);
        
        // Resetar pontos
        ponto1 = null;
        ponto2 = null;
        marker1 = null;
        marker2 = null;
        linha = null;
        
        // Resetar informações
        document.getElementById('ponto1-coords').textContent = "Não selecionado";
        document.getElementById('ponto2-coords').textContent = "Não selecionado";
        document.getElementById('cep1').textContent = "-";
        document.getElementById('cep2').textContent = "-";
        document.getElementById('distancia').textContent = "-";
    });
    
    // Botão Calcular
    document.getElementById('btn-calcular').addEventListener('click', function() {
        if (!ponto1 || !ponto2) {
            alert("Por favor, selecione dois pontos no mapa primeiro.");
            return;
        }
        
        // Mostrar indicador de carregamento
        document.getElementById('distancia').textContent = "Calculando...";
        document.getElementById('cep1').textContent = "Buscando...";
        document.getElementById('cep2').textContent = "Buscando...";
        
        // Validar formato dos pontos
        if (!ponto1.lat || !ponto1.lng || !ponto2.lat || !ponto2.lng) {
            alert("Erro: Coordenadas inválidas.");
            resetarInfos();
            return;
        }
        
        console.log("Enviando pontos para cálculo:", ponto1, ponto2);
        
        // Enviar pontos para a API
        fetch('/api/calcular', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ponto1: ponto1,
                ponto2: ponto2
            })
        })
        .then(response => {
            // Verificar se a resposta foi bem-sucedida
            if (!response.ok) {
                throw new Error(`Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Resposta recebida:", data);
            
            // Verificar se a resposta contém um erro
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Atualizar informações
            document.getElementById('distancia').textContent = `${data.distancia} km`;
            
            // CEP 1
            let textoCep1 = data.cep1.cep;
            if (data.cep1.tipo === "aproximado") {
                textoCep1 += " (aproximado)";
            } else if (data.cep1.tipo === "cidade") {
                textoCep1 += " (cidade)";
            }
            document.getElementById('cep1').textContent = textoCep1;
            
            // CEP 2
            let textoCep2 = data.cep2.cep;
            if (data.cep2.tipo === "aproximado") {
                textoCep2 += " (aproximado)";
            } else if (data.cep2.tipo === "cidade") {
                textoCep2 += " (cidade)";
            }
            document.getElementById('cep2').textContent = textoCep2;
        })
        .catch(error => {
            console.error('Erro:', error);
            alert("Ocorreu um erro ao calcular a distância e obter os CEPs. Detalhes: " + error.message);
            resetarInfos();
        });
        
        function resetarInfos() {
            document.getElementById('distancia').textContent = "-";
            document.getElementById('cep1').textContent = "-";
            document.getElementById('cep2').textContent = "-";
        }
    });
});