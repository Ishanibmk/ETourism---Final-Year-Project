from flask import Flask, render_template, request, jsonify
from utils.algorithm import run_harmony_search, load_distance_matrix
from utils.api_helpers import build_real_conditions_matrix

app = Flask(__name__)

# API Keys (move to .env in production)
G_API_KEY = 'YOUR_GOOGLE_API_KEY'
W_API_KEY = 'YOUR_WEATHER_API_KEY'

@app.route('/')
def index():
    _, city_names = load_distance_matrix('city_distance.csv')
    return render_template('index.html', cities=city_names)

@app.route('/tsp', methods=['POST'])
def tsp():
    data = request.json
    selected_cities = data['cities']
    start_city = data['start_city']

    # Load full distance matrix and city names
    distance_matrix, city_names = load_distance_matrix('city_distance.csv')

    # Indices of selected cities in the full list
    indices = [city_names.index(city) for city in selected_cities]

    # Filter matrices for selected cities
    filtered_distance = [[distance_matrix[i][j] for j in indices] for i in indices]
    traffic_matrix, weather_matrix = build_real_conditions_matrix(city_names, G_API_KEY, W_API_KEY)
    filtered_traffic = [[traffic_matrix[i][j] for j in indices] for i in indices]
    filtered_weather = [[weather_matrix[i][j] for j in indices] for i in indices]

    # Start index in filtered list
    start_index = selected_cities.index(start_city)

    # Run optimization
    path, cost = run_harmony_search(filtered_distance, filtered_traffic, filtered_weather, start_index)
    city_path = [selected_cities[i] for i in path]

    # Extract weather and traffic along the best path
    weather_along_path = []
    traffic_along_path = []
    for i in range(len(path) - 1):
        from_idx = path[i]
        to_idx = path[i+1]
        weather_along_path.append(filtered_weather[from_idx][to_idx])
        traffic_along_path.append(filtered_traffic[from_idx][to_idx])

    return jsonify({
        'best_path': city_path,
        'total_cost': round(cost, 2),
        'weather_along_path': weather_along_path,
        'traffic_along_path': traffic_along_path
    })

if __name__ == '__main__':
    app.run(debug=True)
