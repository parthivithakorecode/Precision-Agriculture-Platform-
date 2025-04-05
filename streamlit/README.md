# Streamlit Dashboard

This is a Streamlit Dashboard that monitors and displays real-time data on humidity, temperature, and soil moisture using the Anedya API. The dashboard is built using Streamlit and Altair for data visualization.

## Features

- **Real-time Data Monitoring**: Automatically refreshes every 10 seconds to provide up-to-date data.
- **User Authentication**: Simple login mechanism to access the dashboard.
- **Data Visualization**: Interactive charts for humidity, temperature, and soil moisture using Altair.

## Installation

To run this project, you'll need to have Python installed. Follow the steps below to set up and run the project:

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/smart-agriculture-dashboard.git
    cd smart-agriculture-dashboard
    ```

2. **Create a virtual environment:**
    ```sh
    python -m venv venv
    ```

3. **Activate the virtual environment:**

    - On Windows:
      ```sh
      venv\Scripts\activate
      ```
    - On macOS and Linux:
      ```sh
      source venv/bin/activate
      ```

4. **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. **Run the Streamlit app:**
    ```sh
    streamlit run Home.py
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


## Configuration

- **Node ID and API Key:**
  The `nodeId` and `apiKey` used to interact with the Anedya API are hardcoded in the `utils/anedya.py` files. Replace these with your actual values obtained from the Anedya dashboard.

## Dependencies

- `streamlit`: Web framework for creating the dashboard.
- `pandas`: Data manipulation and analysis.
- `altair`: Declarative statistical visualization library.
- `pytz`: World Timezone Definitions for Python.
- `requests`: HTTP library for making API calls.
- `streamlit-autorefresh`: Streamlit component for automatic refresh.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for more details.



