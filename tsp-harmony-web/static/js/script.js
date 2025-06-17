document.getElementById('tsp-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const selectedCities = Array.from(document.getElementById('cities').selectedOptions).map(opt => opt.value);
    const startCity = document.getElementById('start').value;

    if (selectedCities.length < 2) {
        document.getElementById('output').innerHTML = '<div class="text-danger">Please select at least 2 cities.</div>';
        return;
    }
    if (!startCity) {
        document.getElementById('output').innerHTML = '<div class="text-danger">Please select a start city.</div>';
        return;
    }

    const payload = {
        cities: selectedCities,
        start_city: startCity
    };

    document.getElementById('output').innerHTML = '<div>Loading...</div>';

    try {
        const response = await fetch('/tsp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        // Prepare weather/traffic display
        let weatherList = '';
        let trafficList = '';
        if (data.weather_along_path && data.traffic_along_path && data.best_path) {
            weatherList = '<ol>' + data.weather_along_path.map((w, i) =>
                `<li>${data.best_path[i]} → ${data.best_path[i+1]}: <b>${w}</b></li>`
            ).join('') + '</ol>';
            trafficList = '<ol>' + data.traffic_along_path.map((t, i) =>
                `<li>${data.best_path[i]} → ${data.best_path[i+1]}: <b>${t}</b></li>`
            ).join('') + '</ol>';
        }

        document.getElementById('output').innerHTML = `
            <div id="best-path"><strong>Best Path:</strong><br>${JSON.stringify(data.best_path)}</div>
            <div id="total-distance" class="mt-2"><strong>Total Distance:</strong><br>${data.total_cost} km</div>
            <div id="weather-matrix" class="mt-2"><strong>Weather Along Path:</strong>${weatherList}</div>
            <div id="traffic-matrix" class="mt-2"><strong>Traffic Along Path:</strong>${trafficList}</div>
        `;

        // Plot the route on the map
        if (data.best_path) {
            plotRoute(data.best_path);
        }
    } catch (err) {
        document.getElementById('output').innerHTML = '<div class="text-danger">Error: Could not get results.</div>';
    }
});

// Populate start city dropdown based on selected cities
function updateStartCityOptions() {
    const selectedCities = Array.from(document.getElementById('cities').selectedOptions).map(opt => opt.value);
    const startSelect = document.getElementById('start');
    startSelect.innerHTML = '';
    selectedCities.forEach(city => {
        const opt = document.createElement('option');
        opt.value = city;
        opt.text = city;
        startSelect.appendChild(opt);
    });
}

// Listen for changes in city selection
document.getElementById('cities').addEventListener('change', updateStartCityOptions);

// Initialize start city dropdown on page load
window.onload = function() {
    updateStartCityOptions();
    initMap();
};

// Add city coordinates for West Bengal (example, update as needed)
const cityCoords = {
    "kolkata": [22.5726, 88.3639],
    "howrah": [22.5958, 88.2636],
    "kharagpur": [22.3460, 87.2319],
    "haldia": [22.0667, 88.0698],
    "bardhaman": [23.2324, 87.8615],
    "malda": [25.0108, 88.1411],
    "darjeeling": [27.0360, 88.2627],
    "siliguri": [26.7271, 88.3953],
    "asansol": [23.6739, 86.9524],
    "durgapur": [23.5204, 87.3119]
    // Add more cities as needed
};

let map, markersLayer, routeLine;

function initMap() {
    if (map) {
        map.remove();
    }
    map = L.map('map').setView([23.5, 87.5], 7); // Centered on West Bengal
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    markersLayer = L.layerGroup().addTo(map);
}

async function plotRoute(cityPath) {
    if (!map) initMap();
    markersLayer.clearLayers();
    if (routeLine) {
        map.removeLayer(routeLine);
        routeLine = null;
    }

    let latlngs = [];
    cityPath.forEach(city => {
        const coord = cityCoords[city.toLowerCase()];
        if (coord) {
            latlngs.push(coord);
            L.marker(coord).addTo(markersLayer).bindPopup(city);
        }
    });

    // Draw route along roads using OSRM for each segment
    if (latlngs.length > 1) {
        let allRouteCoords = [];
        for (let i = 0; i < latlngs.length - 1; i++) {
            const from = latlngs[i];
            const to = latlngs[i + 1];
            // OSRM expects lon,lat
            const url = `https://router.project-osrm.org/route/v1/driving/${from[1]},${from[0]};${to[1]},${to[0]}?overview=full&geometries=geojson`;
            try {
                const res = await fetch(url);
                const json = await res.json();
                if (json.routes && json.routes.length > 0) {
                    const coords = json.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
                    // Avoid duplicating points
                    if (allRouteCoords.length > 0) coords.shift();
                    allRouteCoords = allRouteCoords.concat(coords);
                }
            } catch (e) {
                // fallback: straight line if OSRM fails
                if (allRouteCoords.length > 0) allRouteCoords.pop();
                allRouteCoords.push(from, to);
            }
        }
        if (allRouteCoords.length > 1) {
            routeLine = L.polyline(allRouteCoords, {color: 'blue', weight: 4}).addTo(map);
            map.fitBounds(routeLine.getBounds(), {padding: [30, 30]});
        }
    }
}

// Initialize map on page load
window.onload = function() {
    updateStartCityOptions();
    initMap();
};