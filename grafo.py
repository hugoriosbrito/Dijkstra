import osmnx as ox
from geopy.geocoders import Nominatim
import time
import folium
import heapq
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import animation

geolocator = Nominatim(user_agent="osmnx_address_router_visualizer_v2")

class Dijkstra:
    def __init__(self, geolocator):
        self.geolocator = geolocator

    @staticmethod #usado para não precisar definir self aqui
    def encontrar_no_por_endereco(grafo_localizacao, address_string, geolocator = geolocator):
        """Geocodifica um endereço e encontra o nó mais próximo no grafo."""
        try:
            location = geolocator.geocode(address_string, timeout=10)
            if location:
                point = (location.latitude, location.longitude)
                print(f"Endereço '{address_string}' geocodificado para {point}")
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
        distancias = {no: float('infinity') for no in grafo.nodes}
        distancias[no_origem] = 0
        predecessores = {no: None for no in grafo.nodes}
        fila_prioridade = [(0, no_origem)]
        visitados = set()

        while fila_prioridade:
            distancia_atual, no_atual = heapq.heappop(fila_prioridade)

            if no_atual in visitados:
                continue

            visitados.add(no_atual)

            if no_atual == no_destino:
                caminho = []
                while no_atual is not None:
                    caminho.append(no_atual)
                    no_atual = predecessores[no_atual]
                return caminho[::-1]

            for vizinho, dados_aresta in grafo[no_atual].items():
                for chave_aresta, atributos_aresta in dados_aresta.items():
                    peso_aresta = atributos_aresta.get(weight, float('infinity'))
                    if peso_aresta == float('infinity'):
                        continue

                    distancia = distancia_atual + peso_aresta

                    if distancia < distancias[vizinho]:
                        distancias[vizinho] = distancia
                        predecessores[vizinho] = no_atual
                        heapq.heappush(fila_prioridade, (distancia, vizinho))

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

#todo: consertar erro de geração de gif
class VisualDijkstra:
    def __init__(self, graph, rota):
        self.graph = graph
        self.rota = rota
        self.pos = nx.spring_layout(graph)

    def update_frame(self, frame_num):
        plt.clf()

        nx.draw(self.graph, self.pos, node_color='lightgray',
                edge_color='lightgray', with_labels=False, node_size=30)

        rota_atual = self.rota[:frame_num + 1]
        if len(rota_atual) > 1:
            arestas = list(zip(rota_atual[:-1], rota_atual[1:]))
            nx.draw_networkx_edges(self.graph, self.pos,
                                   edgelist=arestas, edge_color='red', width=2)
            nx.draw_networkx_nodes(self.graph, self.pos,
                                   nodelist=rota_atual, node_color='red',
                                   node_size=50)

        plt.title(f"Frame: {frame_num + 1}/{len(self.rota)}")
        return plt.gca(),

place = "Salvador, Bahia, Brasil"
G = ox.graph.graph_from_place(place, network_type="drive")
try:
    G = ox.simplify_graph(G)
except:
    pass

grafo_dijkstra = Dijkstra(G)

endereco_origem_str = "Av. Luís Viana Filho, 6775, Salvador, Bahia, Brasil"  # Unijorge Paralela
endereco_destino_str = "Av. Orlando Gomes, 1845, Salvador, Bahia, Brasil"  # Senai Cimatec Piatã

origem = grafo_dijkstra.encontrar_no_por_endereco(G, address_string = endereco_origem_str)
destino = grafo_dijkstra.encontrar_no_por_endereco(G,address_string = endereco_destino_str)

rota = grafo_dijkstra.caminho_mais_curto(G,origem, destino)
if rota is not None:
    grafo_dijkstra.gerar_visualizacao_html(rota, origem=origem, destino=destino,
                                           endereco_origem_str=endereco_origem_str,
                                           endereco_destino_str=endereco_destino_str)

    # consertar geração de gif a partir daqui
    vd = VisualDijkstra(G, rota)
    fig, ax = plt.subplots(figsize=(10, 10))
    frames = len(rota)

    try:
        plt.tight_layout()
        ani = animation.FuncAnimation(fig, vd.update_frame, frames=frames, interval=500, blit=False)

        gif_file = 'rota_animacao.gif'
        ani.save(gif_file, writer='pillow', fps=2)
        print(f"gif salvo com sucesso: '{gif_file}'")
    except Exception as e:
        print(f"Erro ao gerar o GIF: {e}")
    finally:
        plt.close(fig)

