import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import io
import base64

app = dash.Dash(__name__)

# Layout with file upload, axis input, and graph
app.layout = html.Div([
    html.H1("Electropherogram Viewer", style={'textAlign': 'center'}),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload CSV Files'),
        multiple=True
    ),
    html.Div([
        html.Label("X-axis Min:"),
        dcc.Input(id='x-min', type='number', step=0.1),
        html.Label("X-axis Max:"),
        dcc.Input(id='x-max', type='number', step=0.1),
        html.Label("Y-axis Min:"),
        dcc.Input(id='y-min', type='number', step=0.01),
        html.Label("Y-axis Max:"),
        dcc.Input(id='y-max', type='number', step=0.01),
        html.Button("Apply Axis Limits", id='apply-axis', n_clicks=0)
    ], style={'margin-bottom': '20px'}),
    dcc.Graph(
        id='electropherogram-plot',
        config={'modeBarButtonsToAdd': ['drawline']}
    ),
    html.Div(id='integration-bounds', style={'margin-top': '20px'})
])

# Function to parse CSV content
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    return df

selected_points = []

# Callback to update the plot
@app.callback(
    Output('electropherogram-plot', 'figure'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('apply-axis', 'n_clicks'),
     Input('electropherogram-plot', 'clickData')],
    [State('x-min', 'value'),
     State('x-max', 'value'),
     State('y-min', 'value'),
     State('y-max', 'value')]
)
def update_output(list_of_contents, list_of_names, apply_axis, click_data, x_min, x_max, y_min, y_max):
    global selected_points
    fig = go.Figure()
    
    data_traces = []
    
    if list_of_contents is not None:
        for contents, name in zip(list_of_contents, list_of_names):
            df = parse_contents(contents)
            trace = go.Scatter(x=df.iloc[:, 0], y=df.iloc[:, 1], mode='lines', name=name)
            fig.add_trace(trace)
            data_traces.append((df.iloc[:, 0], df.iloc[:, 1]))
    
    # Capture integration points from clickData
    if click_data:
        x_clicked = click_data['points'][0]['x']
        y_clicked = click_data['points'][0]['y']
        selected_points.append((x_clicked, y_clicked))
    
    # Plot integration lines from selected points to y=0
    for x, y in selected_points:
        fig.add_trace(go.Scatter(x=[x, x], y=[0, y], mode='lines', line=dict(color='red', dash='dash'), name='Integration Bound'))
    
    axis_updates = {}
    if x_min is not None and x_max is not None:
        axis_updates['xaxis'] = {'range': [x_min, x_max]}
    if y_min is not None and y_max is not None:
        axis_updates['yaxis'] = {'range': [y_min, y_max]}
    
    if axis_updates:
        fig.update_layout(**axis_updates)
    
    fig.update_layout(title="Electropherograms", xaxis_title="Time", yaxis_title="Intensity")
    return fig

@app.callback(
    Output('integration-bounds', 'children'),
    Input('electropherogram-plot', 'clickData')
)
def update_bounds_display(click_data):
    global selected_points
    if click_data:
        x_clicked = click_data['points'][0]['x']
        y_clicked = click_data['points'][0]['y']
        selected_points.append((x_clicked, y_clicked))
    return html.P(f"Integration Points: {selected_points}")

if __name__ == '__main__':
    app.run_server(debug=True)