import requests
import time

#Get Traffic from Google Distance Matrix API
def get_traffic_time(origin, destination, api_key):
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&departure_time=now&traffic_model=best_guess&key={api_key}"
    response = requests.get(url)
    data = response.json()
    try:
        seconds = data['rows'][0]['elements'][0]['duration_in_traffic']['value']
        return seconds
    except:
        return None

#Get Weather from OpenWeatherMap API
def get_weather_condition(city, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    response = requests.get(url)
    data = response.json()
    try:
        main_weather = data['weather'][0]['main'].lower()
        if main_weather in ['clear']:
            return 'clear'
        elif main_weather in ['clouds', 'drizzle']:
            return 'moderate'
        else:
            return 'bad'
    except:
        return 'moderate'

#Build Traffic and Weather Matrices
def build_real_conditions_matrix(city_names, g_api_key, w_api_key):
    size = len(city_names)
    traffic_matrix = [[None for _ in range(size)] for _ in range(size)]
    weather_matrix = [[None for _ in range(size)] for _ in range(size)]

    for i in range(size):
        for j in range(size):
            if i == j:
                traffic_matrix[i][j] = 'low'
                weather_matrix[i][j] = 'clear'
                continue

            travel_time = get_traffic_time(city_names[i], city_names[j], g_api_key)
            weather = get_weather_condition(city_names[j], w_api_key)

            if travel_time is None:
                traffic_matrix[i][j] = 'medium'
            elif travel_time < 1800:
                traffic_matrix[i][j] = 'low'
            elif travel_time < 3600:
                traffic_matrix[i][j] = 'medium'
            else:
                traffic_matrix[i][j] = 'high'

            weather_matrix[i][j] = weather
            time.sleep(0.5)  # Avoid hitting API rate limits

    return traffic_matrix, weather_matrix