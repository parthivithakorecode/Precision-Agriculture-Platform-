# Smart Agricultural Monitoring System ESP8266 Anedya-IoT-Cloud

> [!WARNING]
> This code is for hobbyists for learning purposes. Not recommended for production use!!

This repository contains two main components: an Arduino-based system for collecting environmental data (temperature, humidity, soil moisture) and a Streamlit dashboard for monitoring and visualizing the collected data in real time.

## Components

1. **v1-mqtt**: Arduino sketch for collecting sensor data and sending it to a server using MQTT.
2. **streamlit**: Streamlit dashboard for visualizing real-time sensor data.

## v1-mqtt: NodeMCU+DHT+Soil Moisture Sensor (MQTT)

This Arduino sketch allows you to connect your device to a WiFi network and send data to a server. It fetches the server time and sends data to the Anedya platform.

> **Warning**: This code is for hobbyists for learning purposes. Not recommended for production use!!

### Set-Up Project in Anedya Dashboard

1. Create an account and log in.
2. Create a new project.
3. Create variables: temperature and humidity.
4. Create a node (e.g., for home- Room1 or study room).

For more details, visit the [Anedya documentation](https://docs.anedya.io/getting-started/quickstart/#create-a-new-project).

### Hardware Set-Up

1. Properly identify your sensor's pins.
2. Connect DHT11 sensor VCC pin to 3V3.
3. Connect DHT11 sensor GND pin to GND.
4. Connect DHT11 sensor signal pin to 5 (Marked D1 On the NodeMCU).
5. Connect Soil Moisture sensor VCC pin to 3V3.
6. Connect Soil Moisture sensor GND pin to GND.
7. Connect Soil Moisture sensor A0 pin to A0 (Marked A0 On the NodeMCU).

### Code Set-Up

1. Replace `<PHYSICAL-DEVICE-UUID>` with your 128-bit UUID of the physical device.
2. Replace `<CONNECTION-KEY>` with your connection key from the node description.
3. Set up your WiFi credentials by replacing `SSID` and `PASSWORD` with your WiFi network's SSID and password.
4. Specify the pin number connected to the DHT sensor.

### Usage

1. Connect your device to a WiFi network.
2. Upload this code to your device.
3. Open the Serial Monitor to view the device's output.
4. The device will connect to the WiFi network, read temperature and humidity data from the DHT sensor, and start sending data to Anedya.

### Dependencies

#### ArduinoJson

1. Open the Arduino IDE.
2. Go to `Sketch > Include Library > Manage Libraries...`.
3. Search for "ArduinoJson".
4. Install the library.

#### Timelib

1. Open the Arduino IDE.
2. Go to `Sketch > Include Library > Manage Libraries...`.
3. Search for "Time".
4. Install the library.

#### PubSubClient

1. Open the Arduino IDE.
2. Go to `Sketch > Include Library > Manage Libraries...`.
3. Search for "PubSubClient".
4. Install the library.

#### DHT-Adafruit

1. Open the Arduino IDE.
2. Go to `Sketch > Include Library > Manage Libraries...`.
3. Search for "DHT".
4. Install the library.

For more information, visit [anedya.io](https://anedya.io).

## streamlit: Streamlit Dashboard

This is a Streamlit Dashboard that monitors and displays real-time data on humidity, temperature, and soil moisture using the Anedya API. The dashboard is built using Streamlit and Altair for data visualization.

### Features

- **Real-time Data Monitoring**: Automatically refreshes every 10 seconds to provide up-to-date data.
- **User Authentication**: Simple login mechanism to access the dashboard.
- **Data Visualization**: Interactive charts for humidity, temperature, and soil moisture using Altair.

### Usage

1. **Run the Streamlit app:**
    ```sh
    streamlit run streamlit/Home.py
    ```

2. **Access the dashboard:**
   Open your web browser and go to `http://localhost:8501`.

3. **Login:**
   Use the following credentials to log in:
   - **Username:** admin
   - **Password:** admin

4. **Dashboard Features:**
   - View real-time data for humidity, temperature, and soil moisture.
   - Interactive charts that allow you to explore the data in detail.
   - Manual refresh and logout options.

### Configuration

- **Node ID and API Key:**
  The `nodeId` and `apiKey` used to interact with the Anedya API are hardcoded in the `utils/anedya.py` file. Replace these with your actual values obtained from the Anedya dashboard.

### Dependencies

- `streamlit`: Web framework for creating the dashboard.
- `pandas`: Data manipulation and analysis.
- `altair`: Declarative statistical visualization library.
- `pytz`: World Timezone Definitions for Python.
- `requests`: HTTP library for making API calls.
- `streamlit-autorefresh`: Streamlit component for automatic refresh.



## Versions

### v1-mqtt (Version 1 - MQTT)

This version of the code allows users to monitor sensor data only. It includes functionality to:
- Read temperature, humidity, and soil moisture data from physical sensors.
- Connect to a WiFi network securely.
- Transmit data to Anedya's server using MQTT.
- Handle basic error conditions and connection retries.

### v2-mqtt-alerts (Version 2 - MQTT with Email Alerts)
> [!WARNING]
> Version 2 is under process 

In Version 2, email alerts have been added for proactive monitoring. Updates include:
- Integration with email alerts to notify users of critical sensor readings.
- Enhanced error handling and reliability improvements.



### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.


