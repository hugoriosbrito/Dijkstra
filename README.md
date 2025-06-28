-----

# 🗺️ Interactive Graph Route Visualizer

This Streamlit application helps you visualize the shortest driving route between two addresses on an interactive map. It uses OpenStreetMap data via **OSMnx**, geocodes addresses with **Nominatim** (Geopy), and visualizes the route using **Folium**.

-----

## ✨ Features

  * **📍 Address Geocoding:** Convert street addresses into geographic coordinates.
  * **🛣️ Street Network Graph Loading:** Load and simplify street networks for selected cities/regions.
  * **🔍 Dijkstra's Algorithm:** Efficiently calculate the shortest path between two points on the street network.
  * **🗺️ Interactive Map Visualization:** Display the calculated route on a dynamic Folium map, complete with origin and destination markers.
  * **📏 Route Distance Calculation:** Provides an estimated total distance for the generated route.
  * **⬇️ Downloadable Map:** Option to download the generated map as a standalone HTML file.
  * **📜 Process Log:** View step-by-step messages about the application's progress.

-----

## 🚀 How to Use

1.  **Enter Origin and Destination Addresses:** Use the input fields to specify your starting and ending points. Default addresses are provided for demonstration.
2.  **Select Graph Location:** Choose a city or region from the dropdown menu. The application will load the street network graph for this area.
3.  **Generate Route Visualization:** Click the "**Generate Route Visualization**" button. The application will then:
      * Load the street network graph for the selected location.
      * Geocode your origin and destination addresses to find the nearest nodes on the graph.
      * Calculate the shortest path using Dijkstra's algorithm.
      * Generate and display an interactive map with the route highlighted.
      * Show the estimated route distance.
4.  **Download Map (Optional):** After the map is generated, you can click "**Download HTML Map**" to save the interactive map to your local machine.
5.  **Review Process Log:** Expand the "**Show/Hide Process Log**" section to see detailed messages about the application's operations.

-----

## ⚙️ Requirements

The application requires the following Python libraries:

  * `streamlit`
  * `osmnx`
  * `geopy`
  * `folium`
  * `networkx`
  * `heapq` (standard library)

You can install these dependencies using pip:

```bash
pip install streamlit osmnx geopy folium networkx
```

-----

## ▶️ Running the Application

1.  Save the code as a Python file (e.g., `app.py`).

2.  Open your terminal or command prompt.

3.  Navigate to the directory where you saved the file.

4.  Run the Streamlit application using the command:

    ```bash
    streamlit run app.py
    ```

    This will open the application in your web browser.

-----
