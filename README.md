# LORAN Visualization
**Status**: *Completed*

## Project Overview
This application is designed to visualize the measurements from an emulated LORAN (Long Range Navigation) system. It connects to a WebSocket server that provides data about the signal arrival times at the base stations, and then calculates the position of the object using multilateration techniques.

## Features

- Connecting to a WebSocket server to receive real-time LORAN data.
- Calculating the object's position using the Time Difference of Arrival (TDOA) method and numerical optimization techniques like Least Squares and Gradient Descent.
- Displaying the calculated object position and the base station locations on a 2D Cartesian graph.
- Allowing the user to adjust the configuration parameters of the LORAN system, such as the object's speed, through a web-based interface.

## Usage

1. Ensure you have Docker installed on your system.
2. Pull the LORAN emulation service Docker image from Docker Hub:
   ```
   docker pull iperekrestov/university:loran-emulation-service
   ```
3. Run the LORAN emulation service container:
   ```
   docker run --name loran-emulator -p 4002:4000 iperekrestov/university:loran-emulation-service
   ```
4. Clone the LORAN Visualization repository:
   ```
   git clone https://github.com/your-username/loran-visualization.git
   ```
5. Navigate to the project directory and install the necessary dependencies:
   ```
   cd loran-visualization
   pip install -r requirements.txt
   ```
6. Start the application:
   ```
   python app.py
   ```

## Implementation Details

The application is built using the following technologies:

- **Python**: The programming language used to develop the application.
- **WebSocket**: A protocol for real-time communication between the client and server.
- **Least Squares and Gradient Descent**: Numerical optimization techniques used to calculate the object's position from the TDOA measurements.
- **Plotly**: A library for creating interactive data visualizations.
