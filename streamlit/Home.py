import streamlit as st
import pandas as pd
import altair as alt
import requests
import json
from streamlit_autorefresh import st_autorefresh
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
from datetime import datetime

from utils.anedya import anedya_config
from utils.anedya import anedya_sendCommand
from utils.anedya import anedya_getValue
from utils.anedya import anedya_setValue
from utils.anedya import fetchHumidityData
from utils.anedya import fetchTemperatureData
from utils.anedya import fetchMoistureData

nodeId = "0195e651-cc0c-731f-96d3-4e89384d3924"  # get it from anedya dashboard -> project -> node 
apiKey = "1eed2864228e1537395bd082cb098f5d29f6d00610d0bb60520a49f3878f1dce"  # aneyda project apikey

st.set_page_config(
    page_title="Smart Agriculture Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load your crop recommendation database
@st.cache_data
def load_crop_data():
    # This is a simplified crop database. In production, you might want to use a more comprehensive database.
    return {
        "rice": {
            "temp_range": [20, 35],
            "humidity_range": [70, 90],
            "moisture_range": [700, 2000],
            "nutrients": {
                "nitrogen": "High (100-120 kg/ha)",
                "phosphorus": "Medium (50-60 kg/ha)",
                "potassium": "Medium (40-60 kg/ha)"
            },
            "growing_season": "Wet season",
            "water_requirement": "High"
        },
        "wheat": {
            "temp_range": [15, 25],
            "humidity_range": [50, 70],
            "moisture_range": [450, 1050],
            "nutrients": {
                "nitrogen": "Medium (80-100 kg/ha)",
                "phosphorus": "Medium (40-50 kg/ha)",
                "potassium": "Low (20-30 kg/ha)"
            },
            "growing_season": "Winter",
            "water_requirement": "Medium"
        },
        "maize": {
            "temp_range": [18, 32],
            "humidity_range": [40, 80],
            "moisture_range": [500, 800],
            "nutrients": {
                "nitrogen": "High (120-150 kg/ha)",
                "phosphorus": "Medium (50-60 kg/ha)",
                "potassium": "Medium (40-60 kg/ha)"
            },
            "growing_season": "Spring/Summer",
            "water_requirement": "Medium"
        },
        "cotton": {
            "temp_range": [20, 35],
            "humidity_range": [40, 60],
            "moisture_range": [400, 700],
            "nutrients": {
                "nitrogen": "Medium (80-100 kg/ha)",
                "phosphorus": "Medium (40-60 kg/ha)",
                "potassium": "High (80-100 kg/ha)"
            },
            "growing_season": "Summer",
            "water_requirement": "Medium"
        },
        "sugarcane": {
            "temp_range": [24, 38],
            "humidity_range": [60, 80],
            "moisture_range": [650, 1200],
            "nutrients": {
                "nitrogen": "High (150-200 kg/ha)",
                "phosphorus": "Medium (60-80 kg/ha)",
                "potassium": "High (100-150 kg/ha)"
            },
            "growing_season": "Year-round (tropical)",
            "water_requirement": "High"
        },
        "potato": {
            "temp_range": [15, 25],
            "humidity_range": [60, 70],
            "moisture_range": [500, 700],
            "nutrients": {
                "nitrogen": "Medium (100-120 kg/ha)",
                "phosphorus": "High (80-100 kg/ha)",
                "potassium": "High (100-120 kg/ha)"
            },
            "growing_season": "Winter/Spring",
            "water_requirement": "Medium"
        },
        "tomato": {
            "temp_range": [20, 30],
            "humidity_range": [50, 70],
            "moisture_range": [400, 600],
            "nutrients": {
                "nitrogen": "Medium (80-100 kg/ha)",
                "phosphorus": "High (60-80 kg/ha)",
                "potassium": "High (80-100 kg/ha)"
            },
            "growing_season": "Summer",
            "water_requirement": "Medium"
        }
    }

# Load your regional crop data
@st.cache_data
def load_regional_crop_data():
    # This would ideally be a more comprehensive database with region-specific crop recommendations
    return {
        "Maharashtra": ["sugarcane", "cotton", "rice", "maize"],
        "Punjab": ["wheat", "rice", "cotton", "maize"],
        "Karnataka": ["rice", "sugarcane", "maize", "cotton"],
        "Tamil Nadu": ["rice", "sugarcane", "cotton", "maize"],
        "Gujarat": ["cotton", "wheat", "rice", "potato"],
        "Andhra Pradesh": ["rice", "cotton", "sugarcane", "maize"],
        "West Bengal": ["rice", "potato", "wheat", "maize"],
        "Uttar Pradesh": ["sugarcane", "wheat", "potato", "rice"],
        # Add more regions as needed
    }

# Get user's location from IP
@st.cache_data(ttl=3600)
def get_location():
    return {
        "ip": "N/A",
        "city": "Jaipur",
        "region": "Rajasthan",
        "country": "IN",
        "loc": "26.9124,75.7873"  # Jaipur coordinates
    }
   

# Get weather data
@st.cache_data(ttl=3600)
def get_weather(lat, lon):
    try:
        api_key = "2a40bf8099e8fb97f8059d34de4f2868"  # Replace with your actual API key
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            return {
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"]
            }
        else:
            return {
                "temperature": "N/A",
                "humidity": "N/A",
                "description": "Weather data unavailable",
                "icon": "01d"
            }
    except Exception as e:
        st.error(f"Error fetching weather: {e}")
        return {
            "temperature": "N/A",
            "humidity": "N/A",
            "description": "Weather data unavailable",
            "icon": "01d"
        }

# Recommend crops based on current conditions
def recommend_crops(temperature, humidity, moisture, location_region=None):
    crop_data = load_crop_data()
    regional_data = load_regional_crop_data()
    
    suitable_crops = []
    
    # Get regionally suitable crops if region is available
    regional_crops = []
    if location_region in regional_data:
        regional_crops = regional_data[location_region]
    
    for crop, criteria in crop_data.items():
        # Check if temperature, humidity and moisture are within suitable range
        temp_ok = criteria["temp_range"][0] <= temperature <= criteria["temp_range"][1]
        humidity_ok = criteria["humidity_range"][0] <= humidity <= criteria["humidity_range"][1]
        moisture_ok = criteria["moisture_range"][0] <= moisture <= criteria["moisture_range"][1]
        
        # Calculate suitability score
        score = 0
        if temp_ok: score += 1
        if humidity_ok: score += 1
        if moisture_ok: score += 1
        if crop in regional_crops: score += 2  # Give bonus for regional suitability
        
        if score >= 2:  # Crop is suitable if at least 2 conditions are met
            suitability_percentage = (score / 5) * 100 if location_region else (score / 3) * 100
            suitable_crops.append({
                "name": crop,
                "suitability": suitability_percentage,
                "temp_status": "Optimal" if temp_ok else "Suboptimal",
                "humidity_status": "Optimal" if humidity_ok else "Suboptimal",
                "moisture_status": "Optimal" if moisture_ok else "Suboptimal",
                "nutrients": criteria["nutrients"],
                "water_requirement": criteria["water_requirement"],
                "growing_season": criteria["growing_season"],
            })
    
    # Sort by suitability score
    return sorted(suitable_crops, key=lambda x: x["suitability"], reverse=True)

# Soil health assessment based on moisture values
def assess_soil_health(moisture):
    if moisture < 300:
        return "Dry", "Insufficient moisture for most crops. Consider irrigation."
    elif moisture < 500:
        return "Moderately Dry", "Adequate for drought-resistant crops but may need irrigation."
    elif moisture < 800:
        return "Good", "Optimal moisture for many crops."
    elif moisture < 1000:
        return "Moist", "Good for water-loving crops but watch for drainage issues."
    else:
        return "Waterlogged", "Excessive moisture. Improve drainage to prevent root diseases."

# Calculate nutrient requirements based on selected crop and current soil conditions
def calculate_nutrient_requirements(crop_name, moisture):
    crop_data = load_crop_data()
    if crop_name in crop_data:
        crop = crop_data[crop_name]
        
        # Simple logic to adjust nutrient recommendations based on moisture
        moisture_factor = 1.0
        if moisture < 400:
            moisture_factor = 0.8  # Reduce nutrients for dry soil
        elif moisture > 800:
            moisture_factor = 1.2  # Increase nutrients for wet soil
        
        adjusted_nutrients = {}
        for nutrient, value in crop["nutrients"].items():
            if "High" in value:
                base_value = int(value.split("(")[1].split("-")[0])
                adjusted_value = int(base_value * moisture_factor)
                adjusted_nutrients[nutrient] = f"High ({adjusted_value}-{adjusted_value + 20} kg/ha)"
            elif "Medium" in value:
                base_value = int(value.split("(")[1].split("-")[0])
                adjusted_value = int(base_value * moisture_factor)
                adjusted_nutrients[nutrient] = f"Medium ({adjusted_value}-{adjusted_value + 20} kg/ha)"
            elif "Low" in value:
                base_value = int(value.split("(")[1].split("-")[0])
                adjusted_value = int(base_value * moisture_factor)
                adjusted_nutrients[nutrient] = f"Low ({adjusted_value}-{adjusted_value + 10} kg/ha)"
            else:
                adjusted_nutrients[nutrient] = value
                
        return adjusted_nutrients
    return None

# V-space helper function
def V_SPACE(lines):
    for _ in range(lines):
        st.write("&nbsp;")

# Configure auto-refresh
st_autorefresh(interval=60000, limit=None, key="auto-refresh-handler")

# Initialize global dataframes
humidityData = pd.DataFrame()
temperatureData = pd.DataFrame()
moistureData = pd.DataFrame()

def main():
    anedya_config(nodeId, apiKey)
    global humidityData, temperatureData, moistureData
    
    # Initialize session state variables
    if "LoggedIn" not in st.session_state:
        st.session_state.LoggedIn = False
    if "CurrentHumidity" not in st.session_state:
        st.session_state.CurrentHumidity = 0
    if "CurrentTemperature" not in st.session_state:
        st.session_state.CurrentTemperature = 0
    if "CurrentMoisture" not in st.session_state:
        st.session_state.CurrentMoisture = 0
    if "SelectedCrop" not in st.session_state:
        st.session_state.SelectedCrop = None
    if "DarkMode" not in st.session_state:
        st.session_state.DarkMode = False
        
    # Custom CSS for dark mode
    if st.session_state.DarkMode:
        st.markdown("""
        <style>
        .stApp {
            background-color: #121212;
            color: #FFFFFF;
        }
        .stMetric {
            background-color: #1E1E1E !important;
            border-radius: 8px;
            padding: 15px;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1E1E1E;
        }
        .stTabs [data-baseweb="tab"] {
            color: #FFFFFF;
        }
        .stDataFrame {
            background-color: #1E1E1E;
        }
        </style>
        """, unsafe_allow_html=True)
    
    if st.session_state.LoggedIn is False:
        drawLogin()
    else:
        humidityData = fetchHumidityData()
        temperatureData = fetchTemperatureData()
        moistureData = fetchMoistureData()
        
        drawDashboard()

def drawLogin():
    cols = st.columns([1, 0.8, 1], gap='small')
    with cols[0]:
        pass
    with cols[1]:
        st.title("Smart Agriculture Dashboard", anchor=False)
        st.image("https://iotdesignpro.com/sites/default/files/inline-images/Smart-Greenhouses.jpg", width=150)  # Replace with your own logo
        
        with st.form("login_form"):
            username_inp = st.text_input("Username")
            password_inp = st.text_input("Password", type="password")
            submit_button = st.form_submit_button(label="Login")
            
            if submit_button:
                if username_inp == "admin" and password_inp == "admin":
                    st.session_state.LoggedIn = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials!")
                    
        st.info("👨‍🌾 Welcome to smart agriculture monitoring system. Login to access your farm's data and analysis.")
    with cols[2]:
        pass

def drawDashboard():
    # Sidebar
    with st.sidebar:
        st.title("Farm Controls")
        
        # User profile section
        st.subheader("User Profile")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("https://iotdesignpro.com/sites/default/files/inline-images/Smart-Greenhouses.jpg", width=50)  # Placeholder user avatar
        with col2:
            st.write("Welcome, Admin")
            st.write("Farm: Demo Farm")
        
        # Get location
        location_data = get_location()
        
        # Display location info
        st.subheader("Farm Location")
        st.write(f"📍 {location_data['city']}, {location_data['region']}")
        st.write(f"🌎 {location_data['country']}")
        
        # Dark mode toggle
        dark_mode = st.toggle("Dark Mode", value=st.session_state.DarkMode)
        if dark_mode != st.session_state.DarkMode:
            st.session_state.DarkMode = dark_mode
            st.rerun()
        
        # Logout button
        if st.button("Logout", type="primary"):
            st.session_state.LoggedIn = False
            st.rerun()
    
    # Main Content
    st.title("Smart Agriculture Dashboard", anchor=False)
    
    # Current time
    current_time = datetime.now().strftime("%d %B %Y, %H:%M:%S")
    st.write(f"Last updated: {current_time}")
    
    # Tabs
    tabs = st.tabs(["Dashboard", "Crop Recommendations", "Field Analysis", "Weather", "Settings"])
    
    with tabs[0]:  # Dashboard Tab
        # Current metrics section
        st.subheader("Current Farm Metrics", anchor=False)
        cols = st.columns(3, gap="medium")
        with cols[0]:
            st.metric(
                label="Humidity", 
                value=f"{st.session_state.CurrentHumidity} %",
                delta=round(st.session_state.CurrentHumidity - 60, 1) if st.session_state.CurrentHumidity > 0 else None,
                delta_color="inverse"
            )
        with cols[1]:
            st.metric(
                label="Temperature", 
                value=f"{st.session_state.CurrentTemperature} °C",
                delta=round(st.session_state.CurrentTemperature - 25, 1) if st.session_state.CurrentTemperature > 0 else None,
                delta_color="inverse"
            )
        with cols[2]:
            moisture_value = st.session_state.CurrentMoisture
            soil_state, _ = assess_soil_health(moisture_value)
            st.metric(
                label=f"Soil Moisture ({soil_state})", 
                value=f"{moisture_value}",
                delta=round(moisture_value - 600, 1) if moisture_value > 0 else None,
                delta_color="normal"
            )
        
        # Data visualization section
        chart_cols = st.columns(2)
        
        with chart_cols[0]:
            st.subheader("24-Hour Humidity Trend", anchor=False)
            if humidityData.empty:
                st.info("No humidity data available!")
            else:
                humidity_chart_an = alt.Chart(data=humidityData).mark_area(
                    line={'color': '#1fff7c'},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='#1fff7c', offset=1),
                               alt.GradientStop(color='rgba(255,255,255,0)', offset=0)],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                    interpolate='monotone',
                    cursor='crosshair'
                ).encode(
                    x=alt.X(
                        shorthand="Datetime:T",
                        axis=alt.Axis(format="%H:%M", title="Time", tickCount=6, grid=True),
                    ),
                    y=alt.Y(
                        "aggregate:Q",
                        scale=alt.Scale(domain=[0, 100]),
                        axis=alt.Axis(title="Humidity (%)", grid=True, tickCount=5),
                    ),
                    tooltip=[alt.Tooltip('Datetime:T', format="%Y-%m-%d %H:%M:%S", title="Time",),
                            alt.Tooltip('aggregate:Q', format="0.2f", title="Value")],
                ).properties(height=300).interactive()
                
                st.altair_chart(humidity_chart_an, use_container_width=True)
                
            st.subheader("24-Hour Moisture Trend", anchor=False)
            if moistureData.empty:
                st.info("No moisture data available!")
            else:
                moisture_chart_an = alt.Chart(data=moistureData).mark_area(
                    line={'color': '#1fa2ff'},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='#1fa2ff', offset=1),
                               alt.GradientStop(color='rgba(255,255,255,0)', offset=0)],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                    interpolate='monotone',
                    cursor='crosshair'
                ).encode(
                    x=alt.X(
                        shorthand="Datetime:T",
                        axis=alt.Axis(format="%H:%M", title="Time", tickCount=6, grid=True),
                    ),
                    y=alt.Y(
                        "aggregate:Q",
                        scale=alt.Scale(domain=[0, 1100]),
                        axis=alt.Axis(title="Moisture", grid=True, tickCount=5),
                    ),
                    tooltip=[alt.Tooltip('Datetime:T', format="%Y-%m-%d %H:%M:%S", title="Time",),
                            alt.Tooltip('aggregate:Q', format="0.2f", title="Value")],
                ).properties(height=300).interactive()
                
                st.altair_chart(moisture_chart_an, use_container_width=True)
        
        with chart_cols[1]:
            st.subheader("24-Hour Temperature Trend", anchor=False)
            if temperatureData.empty:
                st.info("No temperature data available!")
            else:
                temperature_chart_an = alt.Chart(data=temperatureData).mark_area(
                    line={'color': '#ff1f32'},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='#ff1f32', offset=1),
                               alt.GradientStop(color='rgba(255,255,255,0)', offset=0)],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                    interpolate='monotone',
                    cursor='crosshair'
                ).encode(
                    x=alt.X(
                        shorthand="Datetime:T",
                        axis=alt.Axis(format="%H:%M", title="Time", tickCount=6, grid=True),
                    ),
                    y=alt.Y(
                        "aggregate:Q",
                        scale=alt.Scale(zero=False, domain=[10, 50]),
                        axis=alt.Axis(title="Temperature (°C)", grid=True, tickCount=5),
                    ),
                    tooltip=[alt.Tooltip('Datetime:T', format="%Y-%m-%d %H:%M:%S", title="Time",),
                            alt.Tooltip('aggregate:Q', format="0.2f", title="Value")],
                ).properties(height=300).interactive()
                
                st.altair_chart(temperature_chart_an, use_container_width=True)
            
            # Farm location map
            st.subheader("Farm Location", anchor=False)
            location_data = get_location()
            lat, lon = location_data["loc"].split(",")
            
            # Create map
            m = folium.Map(location=[float(lat), float(lon)], zoom_start=12)
            folium.Marker(
                [float(lat), float(lon)], 
                popup="Farm Location", 
                tooltip="Farm Location",
                icon=folium.Icon(color="green", icon="leaf", prefix="fa")
            ).add_to(m)
            
            # Add the map to the app
            folium_static(m, width=600, height=300)
            
    with tabs[1]:  # Crop Recommendations Tab
        st.header("Crop Recommendations", anchor=False)
        
        # Current conditions
        current_temp = st.session_state.CurrentTemperature
        current_humidity = st.session_state.CurrentHumidity
        current_moisture = st.session_state.CurrentMoisture
        
        # Get user's region for regional crop recommendations
        location_data = get_location()
        user_region = location_data["region"]
        
        # Get recommended crops
        recommended_crops = recommend_crops(
            temperature=current_temp,
            humidity=current_humidity,
            moisture=current_moisture,
            location_region=user_region
        )
        
        # Display recommendations
        if recommended_crops:
            st.subheader("Recommended Crops for Your Current Conditions", anchor=False)
            st.write(f"Based on current temperature ({current_temp}°C), humidity ({current_humidity}%), and soil moisture ({current_moisture}):")
            
            # Display top recommendations as cards
            crop_cols = st.columns(min(3, len(recommended_crops)))
            for i, crop in enumerate(recommended_crops[:3]):
                with crop_cols[i]:
                    st.markdown(f"""
                    <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #ddd; background-color: {'#f8f9fa' if not st.session_state.DarkMode else '#1e1e1e'}">
                        <h3 style="margin-top: 0;">{crop['name'].title()}</h3>
                        <p><strong>Suitability:</strong> {crop['suitability']:.1f}%</p>
                        <p><strong>Temperature:</strong> {crop['temp_status']}</p>
                        <p><strong>Humidity:</strong> {crop['humidity_status']}</p>
                        <p><strong>Moisture:</strong> {crop['moisture_status']}</p>
                        <p><strong>Growing Season:</strong> {crop['growing_season']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Allow selection of crops for detailed analysis
            st.subheader("Select a Crop for Detailed Analysis", anchor=False)
            crop_options = [crop["name"].title() for crop in recommended_crops]
            selected_crop = st.selectbox("Choose a crop", crop_options)
            
            # Update selected crop in session state
            st.session_state.SelectedCrop = selected_crop.lower()
            
            # Show detailed analysis for selected crop
            if selected_crop:
                selected_crop_data = next((crop for crop in recommended_crops if crop["name"].title() == selected_crop), None)
                
                if selected_crop_data:
                    st.subheader(f"Detailed Analysis: {selected_crop}", anchor=False)
                    
                    # Create columns for layout
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        # Nutrient requirements
                        st.write("#### Nutrient Requirements")
                        adjusted_nutrients = calculate_nutrient_requirements(
                            selected_crop_data["name"], 
                            current_moisture
                        )
                        
                        if adjusted_nutrients:
                            for nutrient, value in adjusted_nutrients.items():
                                st.write(f"**{nutrient.title()}:** {value}")
                        
                        # Water requirements
                        st.write("#### Water Requirements")
                        st.write(f"{selected_crop_data['water_requirement']} water requirement")
                        
                        if selected_crop_data['water_requirement'] == "High" and current_moisture < 600:
                            st.warning("⚠️ Current soil moisture is below optimal levels. Consider irrigation.")
                        elif selected_crop_data['water_requirement'] == "Low" and current_moisture > 800:
                            st.warning("⚠️ Current soil moisture is above optimal levels. Check drainage.")
                    
                    with col2:
                        # Visualize suitability
                        st.write("#### Suitability Factors")
                        
                        # Create a dataframe for the chart
                        factors_df = pd.DataFrame({
                            'Factor': ['Temperature', 'Humidity', 'Moisture'],
                            'Status': [
                                1 if selected_crop_data['temp_status'] == 'Optimal' else 0.5,
                                1 if selected_crop_data['humidity_status'] == 'Optimal' else 0.5,
                                1 if selected_crop_data['moisture_status'] == 'Optimal' else 0.5
                            ]
                        })
                        
                        # Create a simple bar chart
                        suitability_chart = alt.Chart(factors_df).mark_bar().encode(
                            x=alt.X('Factor', title=None),
                            y=alt.Y('Status', title='Suitability', scale=alt.Scale(domain=[0, 1])),
                            color=alt.Color('Status:Q', scale=alt.Scale(scheme='greenblue'))
                        ).properties(height=200)
                        
                        st.altair_chart(suitability_chart, use_container_width=True)
                        
                        # Overall suitability score
                        st.metric("Overall Suitability", f"{selected_crop_data['suitability']:.1f}%")
        else:
            st.warning("No crops recommended for current conditions. Check sensor data or try manual input.")
            
    with tabs[2]:  # Field Analysis Tab
        st.header("Field Analysis", anchor=False)
        
        # Soil Health Assessment
        st.subheader("Soil Health Assessment", anchor=False)
        
        current_moisture = st.session_state.CurrentMoisture
        soil_state, recommendation = assess_soil_health(current_moisture)
        
        # Create columns for soil health display
        soil_cols = st.columns([2, 3])
        
        with soil_cols[0]:
            # Visual indicator of soil health
            if soil_state == "Dry":
                soil_color = "#E5A653"
                progress_val = 0.2
            elif soil_state == "Moderately Dry":
                soil_color = "#EEC643"
                progress_val = 0.4
            elif soil_state == "Good":
                soil_color = "#55A630"
                progress_val = 0.7
            elif soil_state == "Moist":
                soil_color = "#4895EF"
                progress_val = 0.85
            else:  # Waterlogged
                soil_color = "#0077B6"
                progress_val = 1.0
                
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
                    <div style="width: {progress_val * 100}%; height: 100%; background-color: {soil_color};"></div>
                </div>
                <h3 style="margin: 0;">{soil_state}</h3>
                <p>Moisture Reading: {current_moisture}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with soil_cols[1]:
            st.markdown(f"""
            <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #ddd; background-color: {'#f8f9fa' if not st.session_state.DarkMode else '#1e1e1e'}">
                <h3>Recommendation:</h3>
                <p>{recommendation}</p>
                <h4>Optimal Actions:</h4>
                <ul>
                    {"<li>Consider irrigation to improve soil moisture levels.</li>" if soil_state == "Dry" or soil_state == "Moderately Dry" else ""}
                    {"<li>Monitor water levels to prevent drought stress.</li>" if soil_state == "Moderately Dry" else ""}
                    {"<li>Maintain current irrigation schedule.</li>" if soil_state == "Good" else ""}
                    {"<li>Reduce irrigation frequency.</li>" if soil_state == "Moist" else ""}
                    {"<li>Improve field drainage immediately.</li>" if soil_state == "Waterlogged" else ""}
                    {"<li>Consider postponing any additional irrigation.</li>" if soil_state == "Moist" or soil_state == "Waterlogged" else ""}
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Field zones analysis
        st.subheader("Field Zones Analysis", anchor=False)
        
        # Create sample zone data
        zones_data = {
            "Zone A (North)": {"moisture": current_moisture - 50, "health": "Good", "notes": "Good drainage, suitable for most crops"},
            "Zone B (Central)": {"moisture": current_moisture, "health": soil_state, "notes": "Primary sensor location, representative of average field conditions"},
            "Zone C (South)": {"moisture": current_moisture + 70, "health": "Moist", "notes": "Lower elevation, tends to retain more water"}
        }
        
        # Display zones in columns
        zone_cols = st.columns(len(zones_data))
        for i, (zone_name, zone_info) in enumerate(zones_data.items()):
            with zone_cols[i]:
                health_color = "#55A630" if zone_info["health"] == "Good" else "#4895EF" if zone_info["health"] == "Moist" else "#EEC643"
                st.markdown(f"""
                <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #ddd; background-color: {'#f8f9fa' if not st.session_state.DarkMode else '#1e1e1e'}">
                    <h3 style="margin-top: 0;">{zone_name}</h3>
                    <p><span style="display: inline-block; width: 15px; height: 15px; border-radius: 50%; background-color: {health_color}; margin-right: 5px;"></span> <strong>Health:</strong> {zone_info["health"]}</p>
                    <p><strong>Moisture:</strong> {zone_info["moisture"]}</p>
                    <p><strong>Notes:</strong> {zone_info["notes"]}</p>
                </div>
                """, unsafe_allow_html=True)
                
        # Irrigation control section
        st.subheader("Irrigation Control", anchor=False)
        
        irrigation_cols = st.columns([1, 1])
        with irrigation_cols[0]:
            # Manual irrigation controls
            st.write("#### Manual Control")
            zones = ["All Zones", "Zone A (North)", "Zone B (Central)", "Zone C (South)"]
            selected_zone = st.selectbox("Select Zone", zones)
            duration = st.slider("Duration (minutes)", 5, 60, 15)
            
            if st.button("Start Irrigation"):
                st.success(f"Irrigation started in {selected_zone} for {duration} minutes")
                
            if st.button("Stop All Irrigation"):
                st.info("All irrigation stopped")
        
        with irrigation_cols[1]:
            # Automated schedule
            st.write("#### Automated Schedule")
            st.write("Current schedule:")
            
            schedule_data = {
                "Zone A (North)": {"time": "06:00", "duration": "20 min", "days": "Mon, Wed, Fri"},
                "Zone B (Central)": {"time": "07:00", "duration": "15 min", "days": "Tue, Thu, Sat"},
                "Zone C (South)": {"time": "05:30", "duration": "10 min", "days": "Mon, Wed, Fri"}
            }
            
            schedule_df = pd.DataFrame(schedule_data).T
            schedule_df.columns = ["Time", "Duration", "Days"]
            schedule_df.index.name = "Zone"
            
            st.dataframe(schedule_df)
            
            if st.button("Edit Schedule"):
                st.info("Schedule editing functionality would open here")
                
    with tabs[3]:  # Weather Tab
        st.header("Weather Forecast", anchor=False)
        
        # Get location data
        location_data = get_location()
        lat, lon = location_data["loc"].split(",")
        
        # Get current weather
        weather_data = get_weather(lat, lon)
        
        # Display current weather
        weather_cols = st.columns([1, 2])
        
        with weather_cols[0]:
            st.subheader("Current Weather", anchor=False)
            if weather_data["temperature"] != "N/A":
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border-radius: 0.5rem; border: 1px solid #ddd; background-color: {'#f8f9fa' if not st.session_state.DarkMode else '#1e1e1e'}">
                    <img src="http://openweathermap.org/img/wn/{weather_data['icon']}@2x.png" style="width: 100px; height: 100px;">
                    <h2 style="margin: 0;">{weather_data['temperature']}°C</h2>
                    <p style="text-transform: capitalize;">{weather_data['description']}</p>
                    <p>Humidity: {weather_data['humidity']}%</p>
                    <p>{location_data['city']}, {location_data['region']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Weather data unavailable. Please check your API key.")
                
        with weather_cols[1]:
            # Create dummy forecast data
            st.subheader("5-Day Forecast", anchor=False)
            
            forecast_data = [
                {"day": "Today", "temp_max": 28, "temp_min": 21, "icon": "01d", "description": "Clear sky"},
                {"day": "Tomorrow", "temp_max": 29, "temp_min": 22, "icon": "02d", "description": "Few clouds"},
                {"day": "Saturday", "temp_max": 30, "temp_min": 23, "icon": "10d", "description": "Light rain"},
                {"day": "Sunday", "temp_max": 27, "temp_min": 20, "icon": "10d", "description": "Moderate rain"},
                {"day": "Monday", "temp_max": 26, "temp_min": 19, "icon": "02d", "description": "Few clouds"}
            ]
            
            # Display forecast as horizontal cards
            forecast_cols = st.columns(len(forecast_data))
            for i, day in enumerate(forecast_data):
                with forecast_cols[i]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.5rem; border-radius: 0.5rem; border: 1px solid #ddd; background-color: {'#f8f9fa' if not st.session_state.DarkMode else '#1e1e1e'}">
                        <p style="font-weight: bold; margin: 0;">{day['day']}</p>
                        <img src="http://openweathermap.org/img/wn/{day['icon']}@2x.png" style="width: 50px; height: 50px;">
                        <p style="margin: 0;">{day['temp_max']}° / {day['temp_min']}°</p>
                        <p style="font-size: 0.8rem; margin: 0; text-transform: capitalize;">{day['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Weather alerts
            st.subheader("Weather Alerts", anchor=False)
            
            # Sample alerts
            alerts = [
                {"type": "warning", "message": "Heavy rainfall expected on Sunday. Consider checking field drainage."},
                {"type": "info", "message": "Temperature will rise to 30°C on Saturday. Monitor irrigation needs."}
            ]
            
            for alert in alerts:
                if alert["type"] == "warning":
                    st.warning(alert["message"])
                else:
                    st.info(alert["message"])
            
        # Weather impact on crops
        st.subheader("Weather Impact Analysis", anchor=False)
        
        if st.session_state.SelectedCrop:
            crop_name = st.session_state.SelectedCrop
            
            st.write(f"#### Impact on {crop_name.title()}")
            
            # Create sample impact data
            impact_data = {
                "rice": {
                    "rain_impact": "Positive: Rice benefits from upcoming rainfall.",
                    "temp_impact": "Neutral: Temperatures within optimal range for rice growth.",
                    "recommendations": "Ensure fields have proper water retention."
                },
                "wheat": {
                    "rain_impact": "Negative: Excessive rainfall may affect wheat quality.",
                    "temp_impact": "Caution: Weekend temperatures may rise above optimal range.",
                    "recommendations": "Check for disease after rainfall. Consider shade protection."
                },
                "maize": {
                    "rain_impact": "Neutral: Light rainfall benefits maize, heavy rain on Sunday may be concerning.",
                    "temp_impact": "Positive: Forecasted temperatures excellent for maize growth.",
                    "recommendations": "Ensure good drainage before Sunday's rainfall."
                },
                "cotton": {
                    "rain_impact": "Caution: Sunday's rainfall may affect cotton quality if fields become waterlogged.",
                    "temp_impact": "Positive: Warm temperatures ideal for cotton development.",
                    "recommendations": "Check drainage systems before weekend rainfall."
                },
                "sugarcane": {
                    "rain_impact": "Positive: All forecasted rainfall beneficial for sugarcane.",
                    "temp_impact": "Positive: Temperatures ideal for sugarcane growth.",
                    "recommendations": "No special precautions needed."
                },
                "potato": {
                    "rain_impact": "Caution: Heavy rainfall may increase disease risk for potatoes.",
                    "temp_impact": "Caution: Weekend temperatures are at upper limit for potatoes.",
                    "recommendations": "Monitor for blight after rainfall. Consider fungicide application."
                },
                "tomato": {
                    "rain_impact": "Negative: Heavy rain may damage tomato fruits and increase disease risk.",
                    "temp_impact": "Positive: Temperatures good for tomato ripening.",
                    "recommendations": "Consider temporary covering before Sunday's rainfall."
                }
            }
            
            # Display impact if crop is in database
            if crop_name in impact_data:
                impact = impact_data[crop_name]
                
                impact_cols = st.columns(3)
                with impact_cols[0]:
                    st.markdown(f"""
                    <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #ddd; background-color: {'#f8f9fa' if not st.session_state.DarkMode else '#1e1e1e'}">
                        <h4 style="margin-top: 0;">Rainfall Impact</h4>
                        <p>{impact['rain_impact']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with impact_cols[1]:
                    st.markdown(f"""
                    <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #ddd; background-color: {'#f8f9fa' if not st.session_state.DarkMode else '#1e1e1e'}">
                        <h4 style="margin-top: 0;">Temperature Impact</h4>
                        <p>{impact['temp_impact']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with impact_cols[2]:
                    st.markdown(f"""
                    <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #ddd; background-color: {'#f8f9fa' if not st.session_state.DarkMode else '#1e1e1e'}">
                        <h4 style="margin-top: 0;">Recommendations</h4>
                        <p>{impact['recommendations']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(f"No specific weather impact analysis available for {crop_name}. Please select a crop on the Crop Recommendations tab.")
        else:
            st.info("Please select a crop on the Crop Recommendations tab to view weather impact analysis.")

    with tabs[4]:  # Settings Tab
        st.header("Settings", anchor=False)
        
        # System settings
        st.subheader("System Settings", anchor=False)
        settings_cols = st.columns(2)
        
        with settings_cols[0]:
            st.write("#### Data Refresh Settings")
            refresh_interval = st.slider("Data Refresh Interval (seconds)", 30, 300, 60)
            
            st.write("#### Notification Settings")
            email_notifications = st.toggle("Email Alerts", True)
            sms_notifications = st.toggle("SMS Alerts", False)
            
            if email_notifications:
                email = st.text_input("Email Address", "admin@example.com")
            
            if sms_notifications:
                phone = st.text_input("Phone Number", "+1234567890")
                
            alert_types = st.multiselect(
                "Select Alert Types",
                ["Critical Soil Moisture", "Temperature Extremes", "Weather Alerts", "System Errors"],
                ["Critical Soil Moisture", "Temperature Extremes"]
            )
            
        with settings_cols[1]:
            st.write("#### Sensor Calibration")
            st.write("Last calibration: 2023-05-15")
            
            if st.button("Calibrate Moisture Sensor"):
                st.success("Moisture sensor calibration initiated")
                
            if st.button("Calibrate Temperature Sensor"):
                st.success("Temperature sensor calibration initiated")
                
            if st.button("Calibrate Humidity Sensor"):
                st.success("Humidity sensor calibration initiated")
                
            st.write("#### Data Management")
            data_retention = st.selectbox(
                "Data Retention Period",
                ["7 days", "30 days", "90 days", "1 year", "Forever"],
                index=1
            )
            
            if st.button("Export Historical Data"):
                st.info("Preparing data export... (This would download a CSV in a real application)")
                
            if st.button("Clear All Data", type="secondary"):
                st.error("This will delete all historical data. This action cannot be undone.")
                
        # Save settings button
        if st.button("Save Settings", type="primary"):
            st.success("Settings saved successfully")
            
        # Advanced settings
        with st.expander("Advanced Settings"):
            st.write("#### API Configuration")
            api_key_input = st.text_input("API Key", apiKey, type="password")
            node_id_input = st.text_input("Node ID", nodeId)
            
            st.write("#### Diagnostic Tools")
            if st.button("Run System Diagnostic"):
                st.info("Running system diagnostic...")
                st.success("All systems operational")
                
            if st.button("Restart Sensors"):
                st.info("Sending restart command to sensors...")
                st.success("Sensors restarted successfully")
                
        # About section
        with st.expander("About"):
            st.write("#### Smart Agriculture Dashboard")
            st.write("Version 1.0.0")
            st.write("© 2023 Smart Agriculture Solutions")
            st.write("Powered by Streamlit and Anedya IoT Platform")
            st.write("For support, contact support@smartagriculture.example.com")

# Function to update sensor data
def update_sensor_data():
    try:
        # Get the latest data from sensors
        humidity = anedya_getValue("humnow")
        temperature = anedya_getValue("tempnow")
        moisture = anedya_getValue("moistnow")
        
        # Update session state
        if humidity is not None:
            st.session_state.CurrentHumidity = round(float(humidity), 1)
        if temperature is not None:
            st.session_state.CurrentTemperature = round(float(temperature), 1)
        if moisture is not None:
            st.session_state.CurrentMoisture = int(float(moisture))
    except Exception as e:
        st.error(f"Error updating sensor data: {e}")

if __name__ == "__main__":
    # Update sensor data
    update_sensor_data()
    
    # Run the main app
    main()
