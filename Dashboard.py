import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px


# قراءة البيانات ومعالجتها
df = pd.read_csv("noshowappointments.csv")
df['PatientId'] = df['PatientId'].astype('int64')
df['ScheduledDay'] = pd.to_datetime(df['ScheduledDay'])
df['AppointmentDay'] = pd.to_datetime(df['AppointmentDay'])
df["DaysBetween"] = (df["AppointmentDay"] - df["ScheduledDay"]).dt.days

# إنشاء تطبيق Dash
app = dash.Dash(__name__)

# تصميم لوحة التحكم
app.layout = html.Div([
    html.H1("📊 لوحة تحكم تحليل بيانات المواعيد الطبية", style={'textAlign': 'center'}),
    
    html.Label("🔍 اختر الحي:"),
    dcc.Dropdown(
        id="neighbourhood-dropdown",
        options=[{"label": n, "value": n} for n in df["Neighbourhood"].unique()],
        value=df["Neighbourhood"].unique()[0],
        clearable=False
    ),
    
    dcc.Graph(id="days-between-chart"),
    dcc.Graph(id="no-show-pie"),
    dcc.Graph(id="age-distribution"),
    dcc.Graph(id="gender-distribution")
])

# تحديث المخططات بناءً على اختيار الحي
@app.callback(
    Output("days-between-chart", "figure"),
    Output("no-show-pie", "figure"),
    Output("age-distribution", "figure"),
    Output("gender-distribution", "figure"),
    Input("neighbourhood-dropdown", "value")
)
def update_charts(selected_neighbourhood):
    filtered_df = df[df["Neighbourhood"] == selected_neighbourhood]
    
    # توزيع الأيام بين الحجز والموعد
    days_fig = px.histogram(filtered_df, x="DaysBetween", nbins=20,
                            title=f"عدد الأيام بين الحجز والموعد في {selected_neighbourhood}",
                            labels={"DaysBetween": "عدد الأيام"},
                            color_discrete_sequence=["#636EFA"])
    
    # نسبة الغياب عن المواعيد
    no_show_counts = filtered_df["No-show"].value_counts()
    no_show_fig = px.pie(names=no_show_counts.index, values=no_show_counts.values,
                         title=f"نسبة الغياب عن المواعيد في {selected_neighbourhood}",
                         color_discrete_sequence=["#EF553B", "#00CC96"])
    
    # توزيع الفئات العمرية
    age_fig = px.histogram(filtered_df, x="Age", nbins=15,
                           title=f"توزيع الفئات العمرية في {selected_neighbourhood}",
                           labels={"Age": "العمر"},
                           color_discrete_sequence=["#FFA15A"])
    
    # توزيع المرضى حسب الجنس
    gender_counts = filtered_df["Gender"].value_counts()
    gender_fig = px.pie(names=gender_counts.index, values=gender_counts.values,
                        title=f"توزيع المرضى حسب الجنس في {selected_neighbourhood}",
                        color_discrete_sequence=["#AB63FA", "#19D3F3"])
    
    return days_fig, no_show_fig, age_fig, gender_fig

# تشغيل التطبيق
if __name__ == "__main__":
    app.run_server(debug=True)
