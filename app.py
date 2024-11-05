import numpy as np
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import asyncio
import websockets
import json
import requests
import threading

app = dash.Dash(__name__)

def compute_tdoa_error(parameters, x1, y1, x2, y2, x3, y3, delta_t12, delta_t13, speed_of_light):
    x, y = parameters
    distance1 = np.sqrt((x - x1) ** 2 + (y - y1) ** 2)
    distance2 = np.sqrt((x - x2) ** 2 + (y - y2) ** 2)
    distance3 = np.sqrt((x - x3) ** 2 + (y - y3) ** 2)

    delta_t12_calculated = (distance1 - distance2) / speed_of_light
    delta_t13_calculated = (distance1 - distance3) / speed_of_light

    return [
        delta_t12_calculated - delta_t12,
        delta_t13_calculated - delta_t13
    ]

def calculate_loss(parameters, error_func, args):
    errors = error_func(parameters, *args)
    return sum(e ** 2 for e in errors)

def custom_optimizer(error_func, initial_position, args, learning_rate=0.01, max_iterations=10000, tolerance=1e-12):
    x, y = initial_position
    previous_loss = float('inf')

    for iteration in range(max_iterations):
        current_loss = calculate_loss([x, y], error_func, args)

        if abs(previous_loss - current_loss) < tolerance:
            break

        previous_loss = current_loss

        delta = 1e-6
        grad_x = (calculate_loss([x + delta, y], error_func, args) - current_loss) / delta
        grad_y = (calculate_loss([x, y + delta], error_func, args) - current_loss) / delta

        x -= learning_rate * grad_x
        y -= learning_rate * grad_y

    return x, y, iteration

station_x_coords = [0, 100000, 0]
station_y_coords = [0, 0, 100000]

plot_figure = go.Figure()
plot_figure.add_trace(go.Scatter(
    x=station_x_coords,
    y=station_y_coords,
    mode='markers',
    name='Stations',
    marker=dict(size=10, color='blue')
))

receiver_trace = plot_figure.add_trace(go.Scatter(
    x=[None],
    y=[None],
    mode='markers',
    name='Estimated Receiver',
    marker=dict(size=10, color='red')
))

def fetch_config():
    response = requests.get("http://localhost:4002/config")
    return response.json()

def change_object_speed(new_speed):
    payload = {"objectSpeed": new_speed}
    response = requests.post("http://localhost:4002/config", json=payload)
    return response.json()

async def websocket_listener():
    uri = "ws://localhost:4002"
    try:
        async with websockets.connect(uri) as websocket:
            received_times = {}

            while True:
                data = await websocket.recv()
                json_data = json.loads(data)

                source_id = json_data['sourceId']
                received_at = json_data['receivedAt']
                received_times[source_id] = received_at

                if len(received_times) == 3:
                    t1 = received_times.get("source1")
                    t2 = received_times.get("source2")
                    t3 = received_times.get("source3")

                    if None in [t1, t2, t3]:
                        print("Waiting for all timestamps.")
                        continue

                    delta_t12 = ((t1 - t2) / 1000) * 10e8
                    delta_t13 = ((t1 - t3) / 1000) * 10e8

                    initial_position = [50000, 50000]
                    speed_of_light = 3e8 / 10e8
                    x_optimized, y_optimized, iterations = custom_optimizer(
                        compute_tdoa_error,
                        initial_position,
                        args=(station_x_coords[0], station_y_coords[0],
                              station_x_coords[1], station_y_coords[1],
                              station_x_coords[2], station_y_coords[2],
                              delta_t12, delta_t13, speed_of_light)
                    )

                    update_plot(x_optimized, y_optimized)
                    received_times.clear()

    except Exception as e:
        print(f"WebSocket error: {e}")

def update_plot(receiver_x, receiver_y):
    plot_figure.data[1].x = [receiver_x]
    plot_figure.data[1].y = [receiver_y]
    return plot_figure

@app.callback(
    Output('live-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def refresh_graph(n):
    return plot_figure

@app.callback(
    Output('speed-response', 'children'),
    Input('submit-speed', 'n_clicks'),
    State('speed-input', 'value')
)
def adjust_speed(n_clicks, speed):
    if n_clicks is None or speed is None:
        return "Enter speed and click 'Change Speed'."
    try:
        speed = float(speed)
        response = change_object_speed(speed)
        return f"Object speed changed to: {response.get('objectSpeed', 'unknown')} km/h"
    except ValueError:
        return "Enter a valid speed value."

app.layout = html.Div([
    dcc.Graph(id='live-graph', animate=True),
    dcc.Interval(
        id='interval-component',
        interval=1000, 
        n_intervals=0
    ),
    html.Div([
        dcc.Input(id='speed-input', type='number', placeholder='Enter speed (km/h)'),
        html.Button('Change Speed', id='submit-speed', n_clicks=0),
    ]),
    html.Div(id='speed-response', style={'margin-top': '10px'})
])

def start_websocket_thread():
    asyncio.run(websocket_listener())

if __name__ == "__main__":
    config = fetch_config()
    print(f"Current configuration: {config}")

    thread = threading.Thread(target=start_websocket_thread)
    thread.start()

    app.run_server(debug=True)