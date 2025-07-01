# importações necessárias para a implementação
import osmnx as ox  # biblioteca para trabalhar com redes de ruas do OpenStreetMap
from geopy.geocoders import Nominatim  # para geocodificar endereços
import time  # para controle de tempo nas requisições
import folium  # para criar mapas interativos
import heapq  # estrutura de dados heap para implementar fila de prioridade
import networkx as nx  # biblioteca para trabalhar com grafos


# inicializa o geocodificador com um user agent único
geolocator = Nominatim(user_agent="osmnx_address_router_visualizer_v2")

class Dijkstra:
    def __init__(self, geolocator):
        # inicializa a classe com um geocodificador
        self.geolocator = geolocator

    @staticmethod #usado para não precisar definir self aqui
    def encontrar_no_por_endereco(grafo_localizacao, address_string, geolocator = geolocator):
        """Geocodifica um endereço e encontra o nó mais próximo no grafo."""
        try:
            # tenta geocodificar o endereço para obter coordenadas lat/lon
            location = geolocator.geocode(address_string, timeout=10)
            if location:
                # converte as coordenadas em uma tupla (latitude, longitude)
                point = (location.latitude, location.longitude)
                print(f"Endereço '{address_string}' geocodificado para {point}")
                # encontra o nó mais próximo no grafo usando as coordenadas
                nearest_node = ox.nearest_nodes(grafo_localizacao, X=point[1], Y=point[0])
                return nearest_node
            else:
                print(f"Não foi possível geocodificar o endereço: '{address_string}'")
                return None
        except Exception as e:
            print(f"Erro durante a geocodificação ou busca de nó para '{address_string}': {e}")
            return None
        finally:
            time.sleep(1)
            
    @staticmethod
    def caminho_mais_curto(grafo: object, no_origem: int, no_destino: int, weight: object = "length"):
        """
        - grafo: networkx.MultiDiGraph, grafo da rede de ruas
        - no_origem: De onde a gente vai partir
        - no_destino: Pra onde a gente quer chegar
        - weight: Característica que a gente vai usar como peso (tipo 'length', que considera a distância entre os dois pontos apenas)

        Retorna:
        - Lista de nós que formam o caminho mais curto, ou None se não gerar um caminho
        """
        # inicializa as estruturas de dados para o algoritmo de Dijkstra
        distancias = {no: float('infinity') for no in grafo.nodes}  # distância infinita para todos os nós
        distancias[no_origem] = 0  # distância zero para o nó de origem
        predecessores = {no: None for no in grafo.nodes}  # para reconstruir o caminho
        fila_prioridade = [(0, no_origem)]  # fila de prioridade (distância, nó)
        visitados = set()  # conjunto de nós já visitados

        # loop principal do algoritmo de Dijkstra
        while fila_prioridade:
            # remove o nó com menor distância da fila de prioridade
            distancia_atual, no_atual = heapq.heappop(fila_prioridade)

            # se o nó já foi visitado, pula para o próximo
            if no_atual in visitados:
                continue

            # marca o nó como visitado
            visitados.add(no_atual)

            # se chegou ao destino, reconstrói e retorna o caminho
            if no_atual == no_destino:
                caminho = []
                while no_atual is not None:
                    caminho.append(no_atual)
                    no_atual = predecessores[no_atual]
                return caminho[::-1]  # inverte a lista para ter o caminho da origem ao destino

            # explora todos os vizinhos do nó atual
            for vizinho, dados_aresta in grafo[no_atual].items():
                for chave_aresta, atributos_aresta in dados_aresta.items():
                    # obtém o peso da aresta (distância, tempo, etc.)
                    peso_aresta = atributos_aresta.get(weight, float('infinity'))
                    if peso_aresta == float('infinity'):
                        continue  # pula arestas sem peso válido

                    # calcula a nova distância até o vizinho
                    distancia = distancia_atual + peso_aresta

                    # se encontrou um caminho mais curto, atualiza as distancias e predecessores
                    if distancia < distancias[vizinho]:
                        distancias[vizinho] = distancia
                        predecessores[vizinho] = no_atual
                        heapq.heappush(fila_prioridade, (distancia, vizinho))

        # se chegou aqui, não existe caminho entre origem e destino
        return None
    
    @staticmethod
    def gerar_visualizacao_html(rota,origem,destino,endereco_origem_str, endereco_destino_str):
        """
        Gera um mapa interativo com a rota mais curta entre dois endereços.
        """
        print("Rota encontrada!")
        distancia_total_km = sum(G.edges[u, v, 0]['length'] for u, v in zip(rota[:-1], rota[1:])) / 1000
        print(f"Distância estimada da rota: {distancia_total_km:.2f} km")
        route_gdf = ox.routing.route_to_gdf(G, rota, weight="length")

        if not route_gdf.empty:
            map_color_route = "#00bae7"
            m = route_gdf.explore(
                tiles="cartodbpositron",
                style_kwds={"weight": 4 , "color": map_color_route},
                tooltip=["name", "length"],
                popup=True,
                legend=True,
                width="100%"
            )
            orig_coords = (G.nodes[origem]['y'], G.nodes[origem]['x'])
            folium.Marker(
                location=orig_coords,
                popup=f"<b>Origem:</b><br>{endereco_origem_str}",
                tooltip="Origem",
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(m)
            dest_coords = (G.nodes[destino]['y'], G.nodes[destino]['x'])
            folium.Marker(
                location=dest_coords,
                popup=f"<b>Destino:</b><br>{endereco_destino_str}",
                tooltip="Destino",
                icon=folium.Icon(color='red', icon='flag', prefix='fa')
            ).add_to(m)

            m.fit_bounds(m.get_bounds())
            map_file_html = f'visualizacao_rota_{endereco_origem_str} - {endereco_destino_str}.html'
            m.save(map_file_html)
            print(f"Mapa salvo em '{map_file_html}'")

place = "Salvador, Bahia, Brasil"

G = ox.graph.graph_from_place(place, network_type="drive")
try:
    G = ox.simplify_graph(G)
except:
    pass

grafo_dijkstra = Dijkstra(G)

endereco_origem_str = "R. Almiro Romualdo da Silva Campinas de Brotas 40275-030, Salvador, Bahia, Brasil"  # unijorge paralela
endereco_destino_str = "Salvador Shopping, Salvador, Bahia, Brasil"  # senai cimatec piatã

origem = grafo_dijkstra.encontrar_no_por_endereco(G, address_string = endereco_origem_str)
destino = grafo_dijkstra.encontrar_no_por_endereco(G,address_string = endereco_destino_str)

rota = grafo_dijkstra.caminho_mais_curto(G,origem, destino)
if rota is not None:
    grafo_dijkstra.gerar_visualizacao_html(rota, origem=origem, destino=destino,
                                           endereco_origem_str=endereco_origem_str,
                                           endereco_destino_str=endereco_destino_str)
