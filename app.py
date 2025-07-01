import streamlit as st
import streamlit.components.v1 as components
import osmnx as ox
from geopy.geocoders import Nominatim
import time
import folium
import heapq
import networkx as nx
import os

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'map_html' not in st.session_state:
    st.session_state.map_html = None

st.set_page_config(layout="wide", page_title="Graph Route Visualizer")

st.title("Interactive Graph Route Visualizer")
st.markdown("---")

@st.cache_resource
def get_geolocator():
    """Initializes and returns the Nominatim geolocator."""
    return Nominatim(user_agent="streamlit_osmnx_graph_app")

@st.cache_resource
def load_graph(place_name):
    """Loads and simplifies the street network graph for a given place."""
    try:
        st.session_state.messages.append(f"Loading street network for {place_name}...")
        G = ox.graph.graph_from_place(place_name, network_type="drive")
        try:
            G = ox.simplify_graph(G)
        except Exception as e:
            st.session_state.messages.append(
                "Could not simplify graph: This graph has already been simplified, cannot simplify it again.. Proceeding with original graph."
            )
        st.session_state.messages.append(f"Street network for {place_name} loaded successfully!")
        return G
    except Exception as e:
        st.error(f"Failed to load street network for '{place_name}': {e}")
        return None

geolocator = get_geolocator()

class Dijkstra:
    def __init__(self, graph, geolocator_instance):
        self.graph = graph
        self.geolocator = geolocator_instance

    def find_node_by_address(self, address_string):
        """Geocodes an address and finds the nearest node in the graph."""
        if not self.graph:
            return None, "Graph not loaded."

        try:
            with st.spinner(f"Geocoding '{address_string}'..."):
                location = self.geolocator.geocode(address_string, timeout=10)
            if location:
                point = (location.latitude, location.longitude)
                st.session_state.messages.append(f"Address '{address_string}' geocoded to {point}")
                nearest_node = ox.nearest_nodes(self.graph, X=point[1], Y=point[0])
                return nearest_node, None
            else:
                return None, f"Could not geocode address: '{address_string}'"
        except Exception as e:
            return None, f"Error during geocoding or node search for '{address_string}': {e}"
        finally:
            time.sleep(1)

    @staticmethod
    def shortest_path(graph: object, start_node: int, end_node: int, weight: str = "length"):
        """
        Finds the shortest path between two nodes in a graph using Dijkstra's algorithm.
        """
        distances = {node: float('infinity') for node in graph.nodes}
        distances[start_node] = 0
        predecessors = {node: None for node in graph.nodes}
        priority_queue = [(0, start_node)]
        visited = set()

        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)

            if current_node in visited:
                continue
            visited.add(current_node)

            if current_node == end_node:
                path = []
                while current_node is not None:
                    path.append(current_node)
                    current_node = predecessors[current_node]
                return path[::-1]

            for neighbor, edge_data_dict in graph[current_node].items():
                for edge_key, edge_attributes in edge_data_dict.items():
                    edge_weight = edge_attributes.get(weight, float('infinity'))
                    if edge_weight == float('infinity'):
                        continue
                    distance = current_distance + edge_weight
                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        predecessors[neighbor] = current_node
                        heapq.heappush(priority_queue, (distance, neighbor))
        return None

    def generate_html_visualization(self, route, origin_node, destination_node, origin_address_str, destination_address_str):
        """
        Generates an interactive Folium map with the shortest route.
        Returns the HTML content of the map.
        """
        if not route:
            return None, "No route to visualize."

        st.write("Route found! Generating visualization...")
        
        total_distance_m = sum(self.graph.edges[u, v, 0]['length'] for u, v in zip(route[:-1], route[1:]))
        total_distance_km = total_distance_m / 1000
        st.write(f"Estimated route distance: **{total_distance_km:.2f} km**")

        route_gdf = ox.routing.route_to_gdf(self.graph, route, weight="length")

        if not route_gdf.empty:
            map_color_route = "#00bae7"
            
            m = route_gdf.explore(
                tiles="cartodbpositron",
                style_kwds={"weight": 6, "color": map_color_route, "opacity": 0.8},
                tooltip=["name", "length"],
                popup=True,
                legend=False,
                width="100%",
                height="500px"
            )

            orig_coords = (self.graph.nodes[origin_node]['y'], self.graph.nodes[origin_node]['x'])
            folium.Marker(
                location=orig_coords, popup=f"<b>Origin:</b><br>{origin_address_str}",
                tooltip="Origin", icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(m)

            dest_coords = (self.graph.nodes[destination_node]['y'], self.graph.nodes[destination_node]['x'])
            folium.Marker(
                location=dest_coords, popup=f"<b>Destination:</b><br>{destination_address_str}",
                tooltip="Destination", icon=folium.Icon(color='red', icon='flag', prefix='fa')
            ).add_to(m)

            m.fit_bounds(m.get_bounds())
            temp_map_file = "temp_route_map.html"
            m.save(temp_map_file)
            
            with open(temp_map_file, "r", encoding="utf-8") as f:
                html_map_content = f.read()
            
            os.remove(temp_map_file)
            return html_map_content, None
        else:
            return None, "Route GeoDataFrame is empty, cannot visualize."

st.write("### Enter Origin and Destination Addresses")

col1, col2 = st.columns(2)
with col1:
    origin_address_input = st.text_input(
        "Origin Address:",
        value="Correios, Salvador, Bahia, Brasil",
        help="Enter the starting address for your route."
    )
with col2:
    destination_address_input = st.text_input(
        "Destination Address:",
        value="Condomínio Brisas Residencial Clube, Salvador, Bahia, Brazil",
        help="Enter the destination address for your route."
    )

st.write("### Select Graph Location")
selected_place = st.selectbox(
    "Choose a city/region for the street network graph:",
    ("Salvador, Bahia, Brasil", "São Paulo, São Paulo, Brasil", "Rio de Janeiro, Rio de Janeiro, Brasil", "New York City, New York, USA"),
    index=0,
    help="The graph will be loaded for this location. Larger areas might take longer."
)

if st.button("Generate Route Visualization", help="Click to find the shortest path and visualize it on a map."):
    st.session_state.messages = []
    st.session_state.map_html = None
    
    if not origin_address_input or not destination_address_input:
        st.warning("Please enter both origin and destination addresses.")
    else:
        with st.spinner("Generating graph visualization... This may take a moment."):
            G = load_graph(selected_place)
            if G:
                dijkstra_solver = Dijkstra(G, geolocator)
                origin_node, origin_error = dijkstra_solver.find_node_by_address(origin_address_input)
                destination_node, dest_error = dijkstra_solver.find_node_by_address(destination_address_input)

                if origin_error: st.error(f"Origin Error: {origin_error}")
                if dest_error: st.error(f"Destination Error: {dest_error}")

                if origin_node is not None and destination_node is not None:
                    st.session_state.messages.append("Finding shortest path...")
                    route = dijkstra_solver.shortest_path(G, origin_node, destination_node)

                    if route:
                        st.session_state.messages.append("Shortest path found!")
                        map_html, map_error = dijkstra_solver.generate_html_visualization(
                            route, origin_node, destination_node, origin_address_input, destination_address_input
                        )
                        if map_html:
                            st.session_state.map_html = map_html
                        else:
                            st.error(f"Error generating map: {map_error}")
                    else:
                        st.warning("No path could be found between the specified origin and destination.")
                else:
                    st.error("Could not find both origin and destination nodes. Please check the addresses.")
            else:
                st.error("Graph could not be loaded for the selected place. Please try again or choose a different location.")


if st.session_state.map_html:
    st.markdown("---")
    st.write("### Generated Route Map:")
    components.html(st.session_state.map_html, height=550, scrolling=True)
    
    st.download_button(
        label="Download HTML Map",
        data=st.session_state.map_html,
        file_name="route_map.html",
        mime="text/html",
        help="Download the interactive map as a standalone HTML file."
    )

if st.session_state.messages:
    with st.expander("Show/Hide Process Log", expanded=True):
        for message in st.session_state.messages:
            st.info(f"{message}")

st.markdown("---")
