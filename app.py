from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def get_coordinates(city_name):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        response = requests.get(url)
        data = response.json()
        if 'results' in data and data['results']:
            return data['results'][0]['latitude'], data['results'][0]['longitude'], data['results'][0]['name'], data['results'][0].get('country', '')
        return None, None, None, None
    except Exception as e:
        print(f"Error fetching coordinates: {e}")
        return None, None, None, None

def get_weather(lat, lon):
    try:
        # Fetching advanced data: Temperature, Humidity, Feels Like, Precipitation, Rain, Wind Speed, and Daily Rain/Prob
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m&daily=precipitation_probability_max,precipitation_sum&timezone=auto"
        response = requests.get(url)
        data = response.json()
        
        weather_info = {}
        
        if 'current' in data:
            current = data['current']
            weather_info['temperature'] = current.get('temperature_2m', 'N/A')
            weather_info['windspeed'] = current.get('wind_speed_10m', 'N/A')
            weather_info['humidity'] = current.get('relative_humidity_2m', 'N/A')
            weather_info['feels_like'] = current.get('apparent_temperature', 'N/A')
            
        # Fetch AQI
        try:
             aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi"
             aqi_response = requests.get(aqi_url)
             aqi_data = aqi_response.json()
             if 'current' in aqi_data:
                 weather_info['aqi'] = aqi_data['current'].get('us_aqi', 'N/A')
             else:
                 weather_info['aqi'] = 'N/A'
        except Exception as e:
             print(f"Error fetching AQI: {e}")
             weather_info['aqi'] = 'N/A'
        
        if 'daily' in data:
            daily = data['daily']
            # Get today's data (index 0)
            if 'precipitation_probability_max' in daily:
                 weather_info['rain_chance'] = daily['precipitation_probability_max'][0]
            else:
                 weather_info['rain_chance'] = 'N/A'
            
            if 'precipitation_sum' in daily:
                weather_info['daily_rain'] = daily['precipitation_sum'][0]
            else:
                weather_info['daily_rain'] = 0
                
        return weather_info
            
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    place_info = None
    error = None

    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            lat, lon, name, country = get_coordinates(city)
            if lat and lon:
                weather = get_weather(lat, lon)
                if weather:
                    weather_data = weather
                    place_info = {'name': name, 'country': country}
                else:
                    error = "Could not retrieve weather data."
            else:
                error = "City not found."
    
    return render_template('index.html', weather=weather_data, place=place_info, error=error)

if __name__ == '__main__':
    app.run(debug=True)
