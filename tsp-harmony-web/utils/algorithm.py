#Import Library
import csv
import random
import requests
import time
import pandas as pd

#Load Distance Matrix
def load_distance_matrix(filename):
    distance_matrix = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        for row in reader:
            distance_matrix.append([int(x) for x in row[1:]])
    return distance_matrix, header[1:]

#Fuzzy Modifier
def fuzzy_condition_modifier(traffic, weather):
    traffic_weights = {'low': 1.0, 'medium': 1.2, 'high': 1.5}
    weather_weights = {'clear': 1.0, 'moderate': 1.1, 'bad': 1.3}
    return traffic_weights[traffic] * weather_weights[weather]

#Fitness Function with Fuzzy Logic
def fuzzy_fitness(path, distance_matrix, traffic_matrix, weather_matrix):
    total_distance = 0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        base_dist = distance_matrix[a][b]
        modifier = fuzzy_condition_modifier(traffic_matrix[a][b], weather_matrix[a][b])
        total_distance += base_dist * modifier
    a, b = path[-1], path[0]
    total_distance += distance_matrix[a][b] * fuzzy_condition_modifier(traffic_matrix[a][b], weather_matrix[a][b])
    return total_distance

#Harmony Search Parameters
HM_SIZE = 10
MAX_ITER = 100

def fuzzy_hmcr(fitness_val, best, worst):
    if worst == best:
        return 0.9
    norm = (fitness_val - best) / (worst - best)
    if norm < 0.33:
        return 0.95
    elif norm < 0.66:
        return 0.7
    else:
        return 0.4

#Harmony Memory Functions
def initialize_harmony_memory(size, start_index):
    other_indices = [i for i in range(size) if i != start_index]
    memory = []
    for _ in range(HM_SIZE):
        random.shuffle(other_indices)
        memory.append([start_index] + other_indices[:])
    return memory

def improvise_new_solution(harmony_memory, current_fit, best_fit, worst_fit, size, start_index):
    HM_CR_dynamic = fuzzy_hmcr(current_fit, best_fit, worst_fit)
    if random.random() < HM_CR_dynamic:
        base = random.choice(harmony_memory)
        new_solution = base[:]
        i, j = random.sample(range(1, size), 2)  # avoid changing start
        new_solution[i], new_solution[j] = new_solution[j], new_solution[i]
    else:
        other = [i for i in range(size) if i != start_index]
        random.shuffle(other)
        new_solution = [start_index] + other
    return new_solution

def update_harmony_memory(harmony_memory, new_solution, distance_matrix, traffic_matrix, weather_matrix):
    harmony_memory.append(new_solution)
    harmony_memory.sort(key=lambda x: fuzzy_fitness(x, distance_matrix, traffic_matrix, weather_matrix))
    return harmony_memory[:HM_SIZE]

#Run Harmony Search
def run_harmony_search(distance_matrix, traffic_matrix, weather_matrix, start_city_index):
    size = len(distance_matrix)
    harmony_memory = initialize_harmony_memory(size, start_city_index)
    best_solution = min(harmony_memory, key=lambda x: fuzzy_fitness(x, distance_matrix, traffic_matrix, weather_matrix))
    best_distance = fuzzy_fitness(best_solution, distance_matrix, traffic_matrix, weather_matrix)

    for _ in range(MAX_ITER):
        fitness_values = [fuzzy_fitness(sol, distance_matrix, traffic_matrix, weather_matrix) for sol in harmony_memory]
        best_fit = min(fitness_values)
        worst_fit = max(fitness_values)
        current_fit = fuzzy_fitness(best_solution, distance_matrix, traffic_matrix, weather_matrix)

        new_solution = improvise_new_solution(harmony_memory, current_fit, best_fit, worst_fit, size, start_city_index)
        new_fit = fuzzy_fitness(new_solution, distance_matrix, traffic_matrix, weather_matrix)

        if new_fit < best_distance:
            best_solution = new_solution
            best_distance = new_fit

        harmony_memory = update_harmony_memory(harmony_memory, new_solution, distance_matrix, traffic_matrix, weather_matrix)

    return best_solution, best_distance

#Creating Distance Matrix
def get_sub_matrix(file: str):
    # Read the CSV file
    df = pd.read_csv(file, index_col='city')

    # Display available cities
    print("Available cities:")
    print(", ".join(df.index))

    # Get user input for selected cities
    selected_cities = input("\nEnter the cities you want to visit (comma-separated): ").strip().split(',')
    selected_cities = [city.strip().lower() for city in selected_cities]

    # Validate selected cities
    invalid_cities = [city for city in selected_cities if city not in df.index.str.lower()]
    if invalid_cities:
        print(f"Error: The following cities are not in the dataset: {', '.join(invalid_cities)}")
        return None

    # Create sub-matrix
    sub_matrix = df.loc[selected_cities, selected_cities]

    return sub_matrix, df.index

