import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from flask import Flask, jsonify
import dash.development as dos

# Load and process the dataset
df = pd.read_csv("noshowappointments.csv")

# Drop unnecessary columns to reduce data size
df.drop(["PatientId", "AppointmentID"], axis=1, inplace=True)

# Rename "No-show" to "No_show" for easier handling in Python
df = df.rename(columns={"No-show": "No_show"})

# Convert date columns to datetime format
df["ScheduledDay"] = pd.to_datetime(df["ScheduledDay"])
df["AppointmentDay"] = pd.to_datetime(df["AppointmentDay"])

# Compute the number of days between scheduling and appointment
df["DaysBetween"] = (df["AppointmentDay"] - df["ScheduledDay"]).dt.days

# Standardize "No_show" column values to avoid case sensitivity issues
df["No_show"] = df["No_show"].str.strip().str.capitalize()  # Ensures "Yes" and "No"

# Filter only categorical columns for bar chart analysis
categorical_columns = df.columns.tolist()
[categorical_columns.remove(x) for x in ["ScheduledDay", "AppointmentDay", "Age", "Neighbourhood", "DaysBetween", "No_show"] ]

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # Required for deployment

# Define the layout with Tabs
app.layout = html.Div([
    html.H1("📊 Medical Appointment Data Dashboard", style={'textAlign': 'center'}),
    dcc.Tabs([  
        # **Tab 1: General Analysis**
        dcc.Tab(label="General Analysis", children=[
            html.Label("🔍 Select The Neighborhood:"),
            dcc.Dropdown(
                id="neighbourhood-dropdown",
                options=[{"label": n, "value": n} for n in df["Neighbourhood"].unique()],
                value=df["Neighbourhood"].unique()[0],
                clearable=False
            ),

            html.Div([
                html.Div([dcc.Graph(id="days-between-chart")], style={'width': '48%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(id="no-show-pie")], style={'width': '48%', 'display': 'inline-block'}),
            ], style={'width': '100%', 'display': 'flex', 'justify-content': 'space-around'}),

            html.Div([
                html.Div([dcc.Graph(id="age-distribution")], style={'width': '48%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(id="gender-distribution")], style={'width': '48%', 'display': 'inline-block'}),
            ], style={'width': '100%', 'display': 'flex', 'justify-content': 'space-around'}),
        ]),

        # **Tab 2: Show/No-Show Analysis**
        dcc.Tab(label="Show/No-Show Analysis", children=[
            html.H3("📊 Effect of Variables on Attendance/No-show Rate"),
            dcc.Dropdown(
                id="bar-variable-dropdown",
                options=[{"label": col, "value": col} for col in categorical_columns],
                value=categorical_columns[0],
                clearable=False
            ),
            dcc.Graph(id="bar-chart")
        ])
    ])
], style={'width': '95%', 'margin': 'auto'})  # Adjust the page width

# Callback to update graphs based on selected neighborhood
@app.callback(
    [
        Output("days-between-chart", "figure"),
        Output("no-show-pie", "figure"),
        Output("age-distribution", "figure"),
        Output("gender-distribution", "figure")
    ],
    [Input("neighbourhood-dropdown", "value")]
)

def update_charts(selected_neighbourhood):
    """Update all charts based on the selected neighborhood"""
    
    filtered_df = df[df["Neighbourhood"] == selected_neighbourhood]
    # Histogram for days between scheduling and appointment
    days_fig = px.histogram(filtered_df, x="DaysBetween", nbins=20,
                            title=f"Days Between Reservation and Appointment in '{selected_neighbourhood}'",
                            labels={"DaysBetween": "Days Between"},
                            color_discrete_sequence=["#636EFA"])
    days_fig.update_layout(height=400, width=500)
    
    # Pie chart for No-show rate
    no_show_counts = filtered_df["No_show"].value_counts()
    no_show_fig = px.pie(names=no_show_counts.index, values=no_show_counts.values,
                         title=f"No-show Rate in '{selected_neighbourhood}'",
                         color_discrete_map={"Yes": "#EF553B", "No": "#00CC96"})
    no_show_fig.update_layout(height=400, width=500)
    
    # Histogram for age distribution
    age_fig = px.histogram(filtered_df, x="Age", nbins=15,
                           title=f"Age Distribution in '{selected_neighbourhood}'",
                           labels={"Age": "Age"},
                           color_discrete_sequence=["#FFA15A"])
    age_fig.update_layout(height=400, width=500)
    
    # Pie chart for gender distribution
    gender_counts = filtered_df["Gender"].value_counts()
    gender_fig = px.pie(names=gender_counts.index, values=gender_counts.values,
                        title=f"Gender Distribution in '{selected_neighbourhood}'",
                        color_discrete_sequence=["#AB63FA", "#19D3F3"])
    gender_fig.update_layout(height=400, width=500)
    
    return days_fig, no_show_fig, age_fig, gender_fig

# Callback to update bar chart for selected variable
@app.callback(
    Output("bar-chart", "figure"),
    Input("bar-variable-dropdown", "value")
)

def update_bar_chart(xVar):
    """Update bar chart based on selected categorical variable"""
    
    # Compute percentage of show/no-show per category
    df_percent = df.groupby("No_show")[xVar].value_counts(normalize=True).unstack("No_show")

    # to DataFrame 
    df_percent = df_percent.reset_index().melt(id_vars=[xVar], var_name="No_show", value_name="Percentage")
    
    # Create bar chart
    fig = px.bar(df_percent, x=xVar, y="Percentage", color="No_show",
                 title=f"Percentage Show/No Show for {xVar}".title(),
                 labels={"Percentage": "Percentage (%)", xVar: xVar.title()},
                 text=df_percent["Percentage"].apply(lambda x: f"{x*100:.2f}%"),
                 color_discrete_map={"Yes": "#00CC96", "No": "#EF553B"},
                 barmode="group")  
    
    # Update layout for readability
    fig.update_layout(
        xaxis_title=xVar.title(),
        yaxis_title="Percentage (%)",
        yaxis_tickformat=".2%",  
        uniformtext_minsize=14, uniformtext_mode='show',

        bargap=0.4,
        height=500, width=1300
    )
    return fig

# Additional route to fetch data as JSON
@server.route("/get_data")
def get_data():
    """API route to return the dataset as JSON"""
    return jsonify(df.to_dict(orient="records"))

# Run the application
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)

