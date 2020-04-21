import pandas as pd
import numpy as np

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import datetime

#####################################################################################################################################
# Boostrap CSS and font awesome . Option 1) Run from codepen directly Option 2) Copy css file to assets folder and run locally
#####################################################################################################################################
external_stylesheets = ['https://codepen.io/unicorndy/pen/GRJXrvP.css','https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css']

#Insert your javascript here. In this example, addthis.com has been added to the web app for people to share their webpage
external_scripts = [{
        'type': 'text/javascript', #depends on your application
        'src': 'insert your addthis.com js here',
    }]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, external_scripts = external_scripts)
app.title = 'Covid19 - Global Dashboard Example'

#for heroku to run correctly
server = app.server

#Overwrite your CSS setting by including style locally
colors = {
    'background': '#2D2D2D',
    'text': '#E1E2E5',
    'figure_text': '#ffffff',
    'confirmed_text':'#3CA4FF',
    'deaths_text':'#f44336',
    'recovered_text':'#5A9E6F',
    'highest_case_bg':'#393939',
    
}

#Creating custom style for local use
divBorderStyle = {
    'backgroundColor' : '#393939',
    'borderRadius': '12px',
    'lineHeight': 0.9,
}

#Creating custom style for local use
boxBorderStyle = {
    'borderColor' : '#393939',
    'borderStyle': 'solid',
    'borderRadius': '10px',
    'borderWidth':2,
}

######################################
# Retrieve data
######################################

# get data directly from github. The data source provided by Johns Hopkins University.
url_confirmed = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
url_deaths = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
url_recovered = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'

# Data can also be saved locally and read from local drive
# url_confirmed = 'time_series_covid19_confirmed_global.csv'
# url_deaths = 'time_series_covid19_deaths_global.csv'
# url_recovered = 'time_series_covid19_recovered_global.csv'

df_confirmed = pd.read_csv(url_confirmed)
df_deaths = pd.read_csv(url_deaths)
df_recovered = pd.read_csv(url_recovered)

##############################################################################################################################
# Moving Singapore to the first row in the datatable (You can choose any country of interest to be display on the first row)
##############################################################################################################################

def df_move1st_sg(df_t):

    #Moving Singapore to the first row in the datatable
    df_t["new"] = range(1,len(df_t)+1)
    df_t.loc[df_t[df_t['Country/Region'] == 'Singapore'].index.values,'new'] = 0
    df_t = df_t.sort_values("new").drop('new', axis=1)
    return df_t

#########################################################################################
# Data preprocessing for getting useful data and shaping data compatible to plotly plot
#########################################################################################

# Total cases
df_confirmed_total = df_confirmed.iloc[:, 4:].sum(axis=0)
df_deaths_total = df_deaths.iloc[:, 4:].sum(axis=0)
df_recovered_total = df_recovered.iloc[:, 4:].sum(axis=0)

# modified deaths dataset for mortality rate calculation
df_deaths_confirmed=df_deaths.copy()
df_deaths_confirmed['confirmed'] = df_confirmed.iloc[:,-1]

#Sorted - df_deaths_confirmed_sorted is different from others, as it is only modified later. Careful of it dataframe structure
df_deaths_confirmed_sorted = df_deaths_confirmed.sort_values(by=df_deaths_confirmed.columns[-2], ascending=False)[['Country/Region',df_deaths_confirmed.columns[-2],df_deaths_confirmed.columns[-1]]]
df_recovered_sorted = df_recovered.sort_values(by=df_recovered.columns[-1], ascending=False)[['Country/Region',df_recovered.columns[-1]]]
df_confirmed_sorted = df_confirmed.sort_values(by=df_confirmed.columns[-1], ascending=False)[['Country/Region',df_confirmed.columns[-1]]]

#Single day increase
df_deaths_confirmed_sorted['24hr'] = df_deaths_confirmed_sorted.iloc[:,-2] - df_deaths.sort_values(by=df_deaths.columns[-1], ascending=False)[df_deaths.columns[-2]]
df_recovered_sorted['24hr'] = df_recovered_sorted.iloc[:,-1] - df_recovered.sort_values(by=df_recovered.columns[-1], ascending=False)[df_recovered.columns[-2]]
df_confirmed_sorted['24hr'] = df_confirmed_sorted.iloc[:,-1] - df_confirmed.sort_values(by=df_confirmed.columns[-1], ascending=False)[df_confirmed.columns[-2]]

#Aggregate the countries with different province/state together
df_deaths_confirmed_sorted_total = df_deaths_confirmed_sorted.groupby('Country/Region').sum()
df_deaths_confirmed_sorted_total=df_deaths_confirmed_sorted_total.sort_values(by=df_deaths_confirmed_sorted_total.columns[0], ascending=False).reset_index()
df_recovered_sorted_total = df_recovered_sorted.groupby('Country/Region').sum()
df_recovered_sorted_total=df_recovered_sorted_total.sort_values(by=df_recovered_sorted_total.columns[0], ascending=False).reset_index()
df_confirmed_sorted_total = df_confirmed_sorted.groupby('Country/Region').sum()
df_confirmed_sorted_total=df_confirmed_sorted_total.sort_values(by=df_confirmed_sorted_total.columns[0], ascending=False).reset_index()

#Modified recovery csv due to difference in number of rows. Recovered will match ['Province/State','Country/Region']column with Confirmed ['Province/State','Country/Region']
df_recovered['Province+Country'] = df_recovered[['Province/State','Country/Region']].fillna('nann').agg('|'.join,axis=1)
df_confirmed['Province+Country'] = df_confirmed[['Province/State','Country/Region']].fillna('nann').agg('|'.join,axis=1)
df_recovered_fill = df_recovered
df_recovered_fill.set_index("Province+Country")
df_recovered_fill.set_index("Province+Country").reindex(df_confirmed['Province+Country'])
df_recovered_fill = df_recovered_fill.set_index("Province+Country").reindex(df_confirmed['Province+Country']).reset_index()
#split Province+Country back into its respective columns
new = df_recovered_fill["Province+Country"].str.split("|", n = 1, expand = True)
df_recovered_fill['Province/State']=new[0]
df_recovered_fill['Country/Region']=new[1]
df_recovered_fill['Province/State'].replace('nann','NaN')
#drop 'Province+Country' for all dataset
df_confirmed.drop('Province+Country',axis=1,inplace=True)
df_recovered.drop('Province+Country',axis=1,inplace=True)
df_recovered_fill.drop('Province+Country',axis=1,inplace=True)

# Data preprocessing for times series countries graph display 
# create temp to store sorting arrangement for all confirm, deaths and recovered.
df_confirmed_sort_temp = df_confirmed.sort_values(by=df_confirmed.columns[-1], ascending=False)

df_confirmed_t = df_move1st_sg(df_confirmed_sort_temp)
df_confirmed_t['Province+Country'] = df_confirmed_t[['Province/State','Country/Region']].fillna('nann').agg('|'.join,axis=1)
df_confirmed_t=df_confirmed_t.drop(['Province/State','Country/Region','Lat','Long'],axis=1).T

df_deaths_t = df_deaths.reindex(df_confirmed_sort_temp.index)
df_deaths_t = df_move1st_sg(df_deaths_t)
df_deaths_t['Province+Country'] = df_deaths_t[['Province/State','Country/Region']].fillna('nann').agg('|'.join,axis=1)
df_deaths_t=df_deaths_t.drop(['Province/State','Country/Region','Lat','Long'],axis=1).T
# take note use reovered_fill df
df_recovered_t = df_recovered_fill.reindex(df_confirmed_sort_temp.index)
df_recovered_t = df_move1st_sg(df_recovered_t)
df_recovered_t['Province+Country'] = df_recovered_t[['Province/State','Country/Region']].fillna('nann').agg('|'.join,axis=1)
df_recovered_t=df_recovered_t.drop(['Province/State','Country/Region','Lat','Long'],axis=1).T

df_confirmed_t.columns = df_confirmed_t.iloc[-1]
df_confirmed_t = df_confirmed_t.drop('Province+Country')

df_deaths_t.columns = df_deaths_t.iloc[-1]
df_deaths_t = df_deaths_t.drop('Province+Country')

df_recovered_t.columns = df_recovered_t.iloc[-1]
df_recovered_t = df_recovered_t.drop('Province+Country')

df_confirmed_t.index=pd.to_datetime(df_confirmed_t.index)
df_deaths_t.index=pd.to_datetime(df_confirmed_t.index)
df_recovered_t.index=pd.to_datetime(df_confirmed_t.index)

# Highest 10 plot data preprocessing
# getting highest 10 countries with confirmed case
name = df_confirmed_t.columns.str.split("|", 1)
df_confirmed_t_namechange=df_confirmed_t.copy()
# name0 = [x[0] for x in name]
name1 = [x[1] for x in name]
df_confirmed_t_namechange.columns = name1
df_confirmed_t_namechange=df_confirmed_t_namechange.groupby(df_confirmed_t_namechange.columns,axis=1).sum()
df_confirmed_t_namechange10 = df_confirmed_t_namechange.sort_values(by=df_confirmed_t_namechange.index[-1], axis=1, ascending=False).iloc[:,:10]
df_confirmed_t_stack = df_confirmed_t_namechange10.stack()
df_confirmed_t_stack=df_confirmed_t_stack.reset_index(level=[0,1])
df_confirmed_t_stack.rename(columns={"level_0": "Date",'level_1':'Countries', 0: "Confirmed"}, inplace=True)
# getting highest 10 countries with deceased case
name = df_deaths_t.columns.str.split("|", 1)
df_deaths_t_namechange=df_deaths_t.copy()
# name0 = [x[0] for x in name]
name1 = [x[1] for x in name]
df_deaths_t_namechange.columns = name1
df_deaths_t_namechange=df_deaths_t_namechange.groupby(df_deaths_t_namechange.columns,axis=1).sum()
df_deaths_t_namechange10 = df_deaths_t_namechange.sort_values(by=df_deaths_t_namechange.index[-1], axis=1, ascending=False).iloc[:,:10]
df_deaths_t_stack = df_deaths_t_namechange10.stack()
df_deaths_t_stack=df_deaths_t_stack.reset_index(level=[0,1])
df_deaths_t_stack.rename(columns={"level_0": "Date",'level_1':'Countries', 0: "Deceased"}, inplace=True)

# Recreate required columns for map data
map_data = df_confirmed[["Province/State", "Country/Region", "Lat", "Long"]]
map_data['Confirmed'] = df_confirmed.loc[:, df_confirmed.columns[-1]]
map_data['Deaths'] = df_deaths.loc[:, df_deaths.columns[-1]]
map_data['Recovered'] = df_recovered_fill.loc[:, df_recovered_fill.columns[-1]]
map_data['Recovered']=map_data['Recovered'].fillna(0).astype(int) #too covert value back to int and fillna with zero
#last 24 hours increase
map_data['Deaths_24hr']=df_deaths.iloc[:,-1] - df_deaths.iloc[:,-2]
map_data['Recovered_24hr']=df_recovered_fill.iloc[:,-1] - df_recovered_fill.iloc[:,-2]
map_data['Confirmed_24hr']=df_confirmed.iloc[:,-1] - df_confirmed.iloc[:,-2]
map_data.sort_values(by='Confirmed', ascending=False,inplace=True)
#Moving Singapore to the first row in the datatable
map_data["new"] = range(1,len(map_data)+1)
map_data.loc[map_data[map_data['Country/Region'] == 'Singapore'].index.values,'new'] = 0
map_data = map_data.sort_values("new").drop('new', axis=1)


#############################################################################
# mapbox_access_token keys, not all mapbox function require token to function. 
#############################################################################
mapbox_access_token = 'insert your token here'

###########################
# functions to create map
###########################

def gen_map(map_data,zoom,lat,lon):
    return {
        "data": [{
            "type": "scattermapbox",  #specify the type of data to generate, in this case, scatter map box is used
            "lat": list(map_data['Lat']),   #for markers location
            "lon": list(map_data['Long']),
            # "hoverinfo": "text",         
            "hovertext": [["Country/Region: {} <br>Province/State: {} <br>Confirmed: {} (+ {} past 24hrs)<br>Deaths: {} (+ {} past 24hrs)<br>Recovered: {} (+ {} past 24hrs)".format(i, j, k, k24, l, l24, m, m24)]
                          for i, j, k, l, m, k24, l24, m24 in zip(map_data['Country/Region'], map_data['Province/State'],
                                                   map_data['Confirmed'], map_data['Deaths'], map_data['Recovered'],
                                                    map_data['Confirmed_24hr'], map_data['Deaths_24hr'], map_data['Recovered_24hr'],)],

            "mode": "markers",
            "name": list(map_data['Country/Region']),
            "marker": {
                    "opacity": 0.7,
                    "size": np.log(map_data['Confirmed'])*4,
            }
        },
        
        ],
        "layout": dict(
            autosize=True,
            height=350,
            font=dict(color=colors['figure_text']),
            titlefont=dict(color=colors['text'], size='14'),
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=0
            ),
            hovermode="closest",
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            legend=dict(font=dict(size=10), orientation='h'),
            mapbox=dict(
                accesstoken=mapbox_access_token,
                style='mapbox://styles/mapbox/dark-v10',
                center=dict(
                    lon=lon,
                    lat=lat,
                ),
                zoom=zoom,
            )
        ),
    }


##############################################
#Functions to create display for highest cases
##############################################

def high_cases(countryname,total,single,color_word='#63b6ff',confirmed_total=1,deaths = False,):

    if deaths:

        percent = (total/confirmed_total)*100
        return html.P([ html.Span(countryname + ' | ' + f"{int(total):,d}",
                             style={'backgroundColor': colors['highest_case_bg'], 'borderRadius': '6px',}),
                    html.Span(' +' + f"{int(single):,d}",
                             style={'color': color_word,'margin':2,'fontWeight': 'bold','fontSize': 14,}),
                    html.Span(f' ({percent:.2f}%)',
                             style={'color': color_word,'margin':2,'fontWeight': 'bold','fontSize': 14,}),
                   ],
                  style={
                        'textAlign': 'center',
                        'color': 'rgb(200,200,200)',
                        'fontsize':12,
                        }       
                )

    return html.P([ html.Span(countryname + ' | ' + f"{int(total):,d}",
                        style={'backgroundColor': colors['highest_case_bg'], 'borderRadius': '6px',}),
            html.Span(' +' + f"{int(single):,d}",
                        style={'color': color_word,'margin':2,'fontWeight': 'bold','fontSize': 14,}),
            ],
            style={
                'textAlign': 'center',
                'color': 'rgb(200,200,200)',
                'fontsize':12,
                }       
        )

#########################################################################
#Convert datetime to Display datetime with following format - 06-Apr-2020
#########################################################################

def datatime_convert(date_str,days_to_add=0):

    format_str = '%m/%d/%y' # The format
    datetime_obj = datetime.datetime.strptime(date_str, format_str)
    datetime_obj += datetime.timedelta(days=days_to_add)
    return datetime_obj.strftime('%d-%b-%Y')

def return_outbreakdays(date_str):
    format_str = '%d-%b-%Y' # The format
    datetime_obj = datetime.datetime.strptime(date_str, format_str).date()

    d0 = datetime.date(2020, 1, 22)
    delta = datetime_obj - d0
    return delta.days

noToDisplay = 8

confirm_cases = []
for i in range(noToDisplay):
    confirm_cases.append(high_cases(df_confirmed_sorted_total.iloc[i,0],df_confirmed_sorted_total.iloc[i,1],df_confirmed_sorted_total.iloc[i,2]))

deaths_cases = []
for i in range(noToDisplay):
    deaths_cases.append(high_cases(df_deaths_confirmed_sorted_total.iloc[i,0],df_deaths_confirmed_sorted_total.iloc[i,1],df_deaths_confirmed_sorted_total.iloc[i,3],'#ff3b4a',df_deaths_confirmed_sorted_total.iloc[i,2],True))

confirm_cases_24hrs = []
for i in range(noToDisplay):
    confirm_cases_24hrs.append(high_cases(df_confirmed_sorted_total.sort_values(by=df_confirmed_sorted_total.columns[-1], ascending=False).iloc[i,0],
                                            df_confirmed_sorted_total.sort_values(by=df_confirmed_sorted_total.columns[-1], ascending=False).iloc[i,1],
                                            df_confirmed_sorted_total.sort_values(by=df_confirmed_sorted_total.columns[-1], ascending=False).iloc[i,2],
                                            ))

deaths_cases_24hrs = []
for i in range(noToDisplay):
    deaths_cases_24hrs.append(high_cases(df_deaths_confirmed_sorted_total.sort_values(by=df_deaths_confirmed_sorted_total.columns[-1], ascending=False).iloc[i,0],
                                            df_deaths_confirmed_sorted_total.sort_values(by=df_deaths_confirmed_sorted_total.columns[-1], ascending=False).iloc[i,1],
                                            df_deaths_confirmed_sorted_total.sort_values(by=df_deaths_confirmed_sorted_total.columns[-1], ascending=False).iloc[i,3],
                                            '#ff3b4a',
                                            df_deaths_confirmed_sorted_total.sort_values(by=df_deaths_confirmed_sorted_total.columns[-1], ascending=False).iloc[i,2],
                                            True))

####################################################
# Prepare plotly figure to attached to dcc component
# Global outbreak Plot 
####################################################
# Change date index to datetimeindex and share x-axis with all the plot
def draw_global_graph(df_confirmed_total,df_deaths_total,df_recovered_total,graph_type='Total Cases'):
    df_confirmed_total.index = pd.to_datetime(df_confirmed_total.index)

    if graph_type == 'Daily Cases':
        df_confirmed_total = (df_confirmed_total - df_confirmed_total.shift(1)).drop(df_confirmed_total.index[0])
        df_deaths_total = (df_deaths_total - df_deaths_total.shift(1)).drop(df_deaths_total.index[0])
        df_recovered_total = (df_recovered_total - df_recovered_total.shift(1)).drop(df_recovered_total.index[0])

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df_confirmed_total.index, y=df_confirmed_total,
                            mode='lines+markers',
                            name='Confirmed',
                            line=dict(color='#3372FF', width=2),
                            fill='tozeroy',))
    fig.add_trace(go.Scatter(x=df_confirmed_total.index, y=df_recovered_total,
                            mode='lines+markers',
                            name='Recovered',
                            line=dict(color='#33FF51', width=2),
                            fill='tozeroy',))
    fig.add_trace(go.Scatter(x=df_confirmed_total.index, y=df_deaths_total,
                            mode='lines+markers',
                            name='Deaths',
                            line=dict(color='#FF3333', width=2),
                            fill='tozeroy',))

    fig.update_layout(
        hovermode='x',
        font=dict(
            family="Courier New, monospace",
            size=14,
            color=colors['figure_text'],
        ),
        legend=dict(
            x=0.02,
            y=1,
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=12,
                color=colors['figure_text']
            ),
            bgcolor=colors['background'],
            borderwidth=5
        ),
        paper_bgcolor=colors['background'],
        plot_bgcolor=colors['background'],
        margin=dict(l=0, 
                    r=0, 
                    t=0, 
                    b=0
                    ),
        height=300,

    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')

    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='#3A3A3A')
    return fig

####################################################
# Function to plot Highest 10 countries cases
####################################################
def draw_highest_10(df_confirmed_t_stack, df_deaths_t_stack, graphHigh10_type='Confirmed Cases'):

    if graphHigh10_type=='Confirmed Cases':
        fig = px.line(df_confirmed_t_stack, x="Date", y="Confirmed", color='Countries',
             color_discrete_sequence = px.colors.qualitative.Light24)
    else:
        fig = px.line(df_deaths_t_stack, x="Date", y="Deceased", color='Countries',
             title='Deceased cases', color_discrete_sequence = px.colors.qualitative.Light24)

    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        font=dict(
            family="Courier New, monospace",
            size=14,
            color=colors['figure_text'],
        ),
        legend=dict(
            x=0.02,
            y=1,
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=9,
                color=colors['figure_text']
            ),
        ),
        paper_bgcolor=colors['background'],
        plot_bgcolor=colors['background'],
        margin=dict(l=0, 
                    r=0, 
                    t=0, 
                    b=0
                    ),
        height=300,

    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')

    # fig.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='#3A3A3A')
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='#3A3A3A')
    return fig


####################################################
# Function to plot Single Country Scatter Plot
####################################################

def draw_singleCountry_Scatter(df_confirmed_t,df_deaths_t,df_recovered_t,selected_row=0, daily_change=False):
    
    if daily_change:
        df_confirmed_t = (df_confirmed_t - df_confirmed_t.shift(1)).drop(df_confirmed_t.index[0])
        df_deaths_t = (df_deaths_t - df_deaths_t.shift(1)).drop(df_deaths_t.index[0])
        df_recovered_t = (df_recovered_t - df_recovered_t.shift(1)).drop(df_recovered_t.index[0])
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_confirmed_t.index, y=df_confirmed_t.iloc[:,selected_row],
                             mode='lines+markers',
                             name='Confirmed',
                             line=dict(color='#3372FF', width=2),
                             fill='tozeroy',))
    fig.add_trace(go.Scatter(x=df_recovered_t.index, y=df_recovered_t.iloc[:,selected_row],
                             mode='lines+markers',
                             name='Recovered',
                             line=dict(color='#33FF51', width=2),
                             fill='tozeroy',))
    fig.add_trace(go.Scatter(x=df_deaths_t.index, y=df_deaths_t.iloc[:,selected_row],
                             mode='lines+markers',
                             name='Deceased',
                             line=dict(color='#FF3333', width=2),
                             fill='tozeroy',))


    new = df_recovered_t.columns[selected_row].split("|", 1)
    if new[0] == 'nann':
        title = new[1]
    else:
        title = new[1] + " - " + new[0]

    fig.update_layout(
        title=title + ' (Total Cases)',
        hovermode='x',
        font=dict(
            family="Courier New, monospace",
            size=14,
            color="#ffffff",
        ),
        legend=dict(
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=12,
                color=colors['figure_text']
            ),
            bgcolor=colors['background'],
            borderwidth=5
        ),
        paper_bgcolor=colors['background'],
        plot_bgcolor=colors['background'],
        margin=dict(l=0, r=0, t=65, b=0),
        height=350,

    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')

    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='#3A3A3A')

    return fig


####################################################
# Function to plot Single Country Bar with scatter Plot
####################################################

def draw_singleCountry_Bar(df_confirmed_t,df_deaths_t,df_recovered_t,selected_row=0,graph_line='Line Chart'):
    

    df_confirmed_t = (df_confirmed_t - df_confirmed_t.shift(1)).drop(df_confirmed_t.index[0])
    df_deaths_t = (df_deaths_t - df_deaths_t.shift(1)).drop(df_deaths_t.index[0])
    df_recovered_t = (df_recovered_t - df_recovered_t.shift(1)).drop(df_recovered_t.index[0])
        
    fig = go.Figure()
    if graph_line=='Line Chart':
        fig.add_trace(go.Bar(x=df_confirmed_t.index, y=df_confirmed_t.iloc[:,selected_row],
                            name='Confirmed',
                            marker_color='#3372FF'
                            ))
        fig.add_trace(go.Bar(x=df_recovered_t.index, y=df_recovered_t.iloc[:,selected_row],
                            name='Recovered',
                            marker_color='#33FF51'
                            ))
        fig.add_trace(go.Bar(x=df_deaths_t.index, y=df_deaths_t.iloc[:,selected_row],
                            name='Deceased',
                            marker_color='#FF3333'
                            ))
  
    else:
        fig.add_trace(go.Scatter(x=df_confirmed_t.index, y=df_confirmed_t.iloc[:,selected_row],
                                mode='lines+markers',
                                name='Confirmed',
                                line=dict(color='#3372FF', width=2),
                                fill='tozeroy',))
        fig.add_trace(go.Scatter(x=df_recovered_t.index, y=df_recovered_t.iloc[:,selected_row],
                                mode='lines+markers',
                                name='Recovered',
                                line=dict(color='#33FF51', width=2),
                                fill='tozeroy',))
        fig.add_trace(go.Scatter(x=df_deaths_t.index, y=df_deaths_t.iloc[:,selected_row],
                                mode='lines+markers',
                                name='Deceased',
                                line=dict(color='#FF3333', width=2),
                                fill='tozeroy',))

    new = df_recovered_t.columns[selected_row].split("|", 1)
    if new[0] == 'nann':
        title = new[1]
    else:
        title = new[1] + " - " + new[0]

    fig.update_layout(
        title=title + ' (Daily Cases)',
        barmode='stack',
        hovermode='x',
        font=dict(
            family="Courier New, monospace",
            size=14,
            color="#ffffff",
        ),
        legend=dict(
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=12,
                color=colors['figure_text']
            ),
            bgcolor=colors['background'],
            borderwidth=5
        ),
        paper_bgcolor=colors['background'],
        plot_bgcolor=colors['background'],
        margin=dict(l=0, r=0, t=65, b=0),
        height=350,
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#3A3A3A')

    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='#3A3A3A')

    return fig

############################
# Bootstrap Grid Layout
############################

app.layout = html.Div(
    html.Div([
        # Header display
        html.Div(
            [
                html.H1(children='Covid-19 (Coronavirus) Interactive Outbreak Tracker',
                        style={
                            'textAlign': 'left',
                            'color': colors['text'],
                            'backgroundColor': colors['background'],
                        },
                        className='ten columns',
                        ),

                html.Div([
                    html.Button(html.I(className="fa fa-info-circle"),
                        id='info-button',
                        style={
                             'color': colors['text'],
                             'fontSize':'36px'

                         },)

                ],className='two columns',),

                # Preload Modal windows and set "display": "none" to hide it first
                html.Div([  # modal div
                    html.Div([  # content div

                        dcc.Markdown('''
                            ##### Dataset provided by Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE):
                            https://systems.jhu.edu/
                           
                            Data Sources:
                            * World Health Organization (WHO): https://www.who.int/
                            * DXY.cn. Pneumonia. 2020. http://3g.dxy.cn/newh5/view/pneumonia.
                            * BNO News: https://bnonews.com/index.php/2020/02/the-latest-coronavirus-cases/
                            * National Health Commission of the People’s Republic of China (NHC):
                            http://www.nhc.gov.cn/xcs/yqtb/list_gzbd.shtml
                            * China CDC (CCDC): http://weekly.chinacdc.cn/news/TrackingtheEpidemic.htm
                            * Hong Kong Department of Health: https://www.chp.gov.hk/en/features/102465.html
                            * Macau Government: https://www.ssm.gov.mo/portal/
                            * Taiwan CDC: https://sites.google.com/cdc.gov.tw/2019ncov/taiwan?authuser=0
                            * US CDC: https://www.cdc.gov/coronavirus/2019-ncov/index.html
                            * Government of Canada: https://www.canada.ca/en/public-health/services/diseases/coronavirus.html
                            * Australia Government Department of Health: https://www.health.gov.au/news/coronavirus-update-at-a-glance
                            * European Centre for Disease Prevention and Control (ECDC): https://www.ecdc.europa.eu/en/geographical-distribution-2019-ncov-cases 
                            * Ministry of Health Singapore (MOH): https://www.moh.gov.sg/covid-19
                            * Italy Ministry of Health: http://www.salute.gov.it/nuovocoronavirus
                            * 1Point3Arces: https://coronavirus.1point3acres.com/en
                            * WorldoMeters: https://www.worldometers.info/coronavirus/
                            '''),
                        html.Hr(),
                        html.Button('Close', id='modal-close-button',
                        style={
                             'color': colors['text'],
                         },)
                    ],
                        style={
                            'fontSize': 10,
                            'lineHeight': 0.9,
                        },
                        className='modal-content',
                    ),
                ],
                    id='modal',
                    className='modal',
                    style={"display": "none"},
                ),

                html.Div([html.Span('Dashboard: Covid-19 outbreak. (Updated once a day, based on consolidated last day total) Last Updated: ',
                             style={'color': colors['text'],
                             }),
                        html.Span(datatime_convert(df_confirmed.columns[-1],1) + '  00:01 (UTC).',
                             style={'color': colors['confirmed_text'],
                             'fontWeight': 'bold',
                             }),

                         ],className='twelve columns'
                         ),
                html.Div([html.Span('Outbreak since 22-Jan-2020: ',
                             style={'color': colors['text'],
                             }),
                        html.Span(str(return_outbreakdays(datatime_convert(df_confirmed.columns[-1],1))) + '  days.',
                             style={'color': colors['confirmed_text'],
                             'fontWeight': 'bold',
                             }),

                         ],
                         className='twelve columns'
                         ),
                html.Div(children='Best viewed on Desktop. Refresh browser for latest update.',
                         style={
                             'textAlign': 'left',
                             'color': colors['text'],
                             'backgroundColor': colors['background'],
                         },
                         className='twelve columns'
                         )
            ], className="row"
        ),

        # Top column display of confirmed, death and recovered total numbers
        html.Div([
            html.Div([
                html.H4(children='Total Cases: ',
                       style={
                           'textAlign': 'center',
                           'color': colors['confirmed_text'],
                       }
                       ),
                html.P(f"{df_confirmed_total[-1]:,d}",
                       style={
                    'textAlign': 'center',
                    'color': colors['confirmed_text'],
                    'fontSize': 30,
                }
                ),
                html.P('Past 24hrs increase: +' + f"{df_confirmed_total[-1] - df_confirmed_total[-2]:,d}"
                       + ' (' + str(round(((df_confirmed_total[-1] - df_confirmed_total[-2])/df_confirmed_total[-1])*100, 2)) + '%)',
                       style={
                    'textAlign': 'center',
                    'color': colors['confirmed_text'],
                }
                ),
            ],
                style=divBorderStyle,
                className='four columns',
            ),
            html.Div([
                html.H4(children='Total Deceased: ',
                       style={
                           'textAlign': 'center',
                           'color': colors['deaths_text'],
                       }
                       ),
                html.P(f"{df_deaths_total[-1]:,d}",
                       style={
                    'textAlign': 'center',
                    'color': colors['deaths_text'],
                    'fontSize': 30,
                }
                ),
                html.P('Mortality Rate: ' + str(round(df_deaths_total[-1]/df_confirmed_total[-1] * 100, 3)) + '%',
                       style={
                    'textAlign': 'center',
                    'color': colors['deaths_text'],
                }
                ),
            ],
                style=divBorderStyle,
                className='four columns'),
            html.Div([
                html.H4(children='Total Recovered: ',
                       style={
                           'textAlign': 'center',
                           'color': colors['recovered_text'],
                       }
                       ),
                html.P(f"{df_recovered_total[-1]:,d}",
                       style={
                    'textAlign': 'center',
                    'color': colors['recovered_text'],
                    'fontSize': 30,
                }
                ),
                html.P('Recovery Rate: ' + str(round(df_recovered_total[-1]/df_confirmed_total[-1] * 100, 3)) + '%',
                       style={
                    'textAlign': 'center',
                    'color': colors['recovered_text'],
                }
                ),
            ],
                style=divBorderStyle,
                className='four columns'),
        ], className='row'),

        # Graph of total confirmed, recovered and deaths
        html.Div(
            [
                html.H4(children='Global Covid-19 cases',
                         style={
                             'textAlign': 'center',
                             'color': colors['text'],
                             'backgroundColor': colors['background'],

                         },
                         className='twelve columns'
                         ),
                html.Div([
                    dcc.RadioItems(
                        id='graph-type',
                        options=[{'label': i, 'value': i}
                                 for i in ['Total Cases', 'Daily Cases']],
                        value='Total Cases',
                        labelStyle={'display': 'inline-block'},
                        style={
                            'fontSize': 20,
                         },
                        
                    )
                ],className='six columns'
                ),
                                html.Div([
                    dcc.RadioItems(
                        id='graph-high10-type',
                        options=[{'label': i, 'value': i}
                                 for i in ['Confirmed Cases', 'Deceased Cases']],
                        value='Confirmed Cases',
                        labelStyle={'display': 'inline-block'},
                        style={
                            'fontSize': 20,
                         },
                        
                    )
                ],className='five columns'
                ),
                html.Div([
                    dcc.Graph(
                        id='global-graph',

                    )
                ], className='six columns'
                ),
                html.Div([
                    dcc.Graph(
                        id='high10-graph',

                    )
                ], className='five columns'
                ),

            ], className="row",
            style={
                'textAlign': 'left',
                'color': colors['text'],
                'backgroundColor': colors['background'],
            },
        ),

        # Highest 5 Countries Display
        # 1x4 grid
        html.Div([
            html.Div([

                    html.P([html.Span('Countries with highest cases: ',
                             ),
                    html.Br(),
                    html.Span(' + past 24hrs',
                             style={'color': colors['confirmed_text'],
                             'fontWeight': 'bold','fontSize': 14,})
                    ],
                    style={
                        'textAlign': 'center',
                        'color': 'rgb(200,200,200)',
                        'fontsize':12,
                        'backgroundColor':'#3B5998',
                        'borderRadius': '12px',
                        'fontSize': 17,
                        }       
                ),
                html.P(confirm_cases),
            ],
                className="three columns",
            ),

            html.Div([
                    html.P([html.Span('Single day highest cases: ',
                             ),
                    html.Br(),
                    html.Span(' + past 24hrs',
                             style={'color': colors['confirmed_text'],
                             'fontWeight': 'bold','fontSize': 14,})
                    ],
                    style={
                        'textAlign': 'center',
                        'color': 'rgb(200,200,200)',
                        'fontsize':12,
                        'backgroundColor':'#3B5998',
                        'borderRadius': '12px',
                        'fontSize': 17,
                        }       
                ),

                html.P(confirm_cases_24hrs),
            ],
                className="three columns",
            ),

            html.Div([
                    html.P([html.Span('Countries with highest mortality: ',
                             ),
                    html.Br(),
                    html.Span(' + past 24hrs (Mortality Rate)',
                             style={'color': '#f2786f',
                             'fontWeight': 'bold','fontSize': 14,})
                    ],
                    style={
                        'textAlign': 'center',
                        'color': 'rgb(200,200,200)',
                        'fontsize':12,
                        'backgroundColor':'#ab2c1a',
                        'borderRadius': '12px',
                        'fontSize': 17,
                        }       
                ),

                html.P(deaths_cases),
            ],
                className="three columns",
            ),
            html.Div([

                    html.P([html.Span('Single day highest mortality: ',
                             ),
                    html.Br(),
                    html.Span(' + past 24hrs (Mortality Rate)',
                             style={'color': '#f2786f',
                             'fontWeight': 'bold','fontSize': 14,})
                    ],
                    style={
                        'textAlign': 'center',
                        'color': 'rgb(200,200,200)',
                        'fontsize':12,
                        'backgroundColor':'#ab2c1a',
                        'borderRadius': '12px',
                        'fontSize': 17,
                        }       
                ),

                html.P(deaths_cases_24hrs),
            ],
                className="three columns",
            ),
        ], className="row",
            style={
            'textAlign': 'left',
            'color': colors['text'],
            'backgroundColor': colors['background'],
                'padding': 20
        },
        ),

        html.Div([
            html.Div(children='Global Outbreak Map - Select row from table to locate in map',
                     style={
                         'textAlign': 'center',
                         'color': colors['text'],
                         'backgroundColor': colors['background'],
                     },
                     className='six columns'
                     ),
        ], className='row'
        ),

        #Map, Table
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id='map-graph',
                                  )
                    ], className="six columns"
                ),
                html.Div(
                    [
                        dt.DataTable(
                            data=map_data.to_dict('records'),
                            columns=[
                                {"name": i, "id": i, "deletable": False, "selectable": True} for i in ['Province/State', 'Country/Region', 'Confirmed',
                                                                                                       'Deaths', 'Recovered']
                            ],
                            fixed_rows={'headers': True, 'data': 0},
                            style_header={
                                'backgroundColor': 'rgb(30, 30, 30)',
                                'fontWeight': 'bold'
                            },
                            style_cell={
                                'backgroundColor': 'rgb(100, 100, 100)',
                                'color': colors['text'],
                                'maxWidth': 0,
                                'fontSize':14,
                            },
                            style_table={
                                'maxHeight': '350px',
                                'overflowY': 'auto'
                            },
                            style_data={
                                'whiteSpace': 'normal',
                                'height': 'auto',

                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'even'},
                                    'backgroundColor': 'rgb(60, 60, 60)',
                                },
                                {
                                    'if': {'column_id' : 'Confirmed'},
                                    'color':colors['confirmed_text'],
                                    'fontWeight': 'bold'
                                },
                                {
                                    'if': {'column_id' : 'Deaths'},
                                    'color':colors['deaths_text'],
                                    'fontWeight': 'bold'
                                },
                                {
                                    'if': {'column_id' : 'Recovered'},
                                    'color':colors['recovered_text'],
                                    'fontWeight': 'bold'
                                },
                                ],
                            style_cell_conditional=[
                                {'if': {'column_id': 'Province/State'},
                                 'width': '26%'},
                                {'if': {'column_id': 'Country/Region'},
                                 'width': '26%'},
                                {'if': {'column_id': 'Confirmed'},
                                 'width': '16%'},
                                {'if': {'column_id': 'Deaths'},
                                 'width': '11%'},
                                {'if': {'column_id': 'Recovered'},
                                 'width': '16%'},
                            ],

                            editable=False,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="single",
                            row_selectable="single",
                            row_deletable=False,
                            selected_columns=[],
                            selected_rows=[],
                            page_current=0,
                            page_size=1000,
                            id='datatable'
                        ),
                    ],
                    className="six columns"
                ),

            ], className="row",
        ),

        #Single country line graph, single country bar graph
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id='line-graph',
                                  )
                    ], className="six columns"
                ),
                html.Div(
                    [
                        dcc.Graph(id='bar-graph',
                                  )
                    ], className="six columns"
                ),

            ], className="row",
            style={
                'textAlign': 'left',
                'color': colors['text'],
                'backgroundColor': colors['background'],
            },
        ),
        html.Div([
            html.Div([html.P()],className='six columns'), #leave a gap of 6 columns
            html.Div([
                dcc.RadioItems(
                    id='graph-line',
                    options=[{'label': i, 'value': i}
                             for i in ['Line Chart', 'Bar Chart']],
                    value='Line Chart',
                    labelStyle={'display': 'inline-block'},
                    style={
                        'fontSize': 20,
                        'textAlign': 'left',
                    },

                )
            ],className="six columns"),

            html.Div(
                    [
                        html.Hr(),
                        html.P('Source Code Hosted on  ',
                               style={'display': 'inline'}),
                        html.A('Github',
                               href='https://github.com/Unicorndy/covid19_dashboard'),
                        html.P(' 2020.',
                            style={'display': 'inline'}),
                        html.P(' Click here to access ',
                            style={'display': 'inline'}),
                        html.A('Covid 19 Version 2.0 Web App',
                               href='https://covid19dashboardsg.herokuapp.com/'),
                        html.Hr(),
                    ], className="twelve columns",
                    style={'fontSize': 18, 'padding-top': 20}
                )
        ],className="row"
        ),


    ],
        className='ten columns offset-by-one'
    ),
    style={
        'textAlign': 'left',
        'color': colors['text'],
        'backgroundColor': colors['background'],
    },
)



@app.callback(
    Output('global-graph', 'figure'),
    [Input('graph-type', 'value')])
def update_graph(graph_type):
    fig_global = draw_global_graph(df_confirmed_total,df_deaths_total,df_recovered_total,graph_type)
    return fig_global

@app.callback(
    Output('high10-graph', 'figure'),
    [Input('graph-high10-type', 'value')])
def update_graph_high10(graph_high10_type):
    fig_high10 = draw_highest_10(df_confirmed_t_stack, df_deaths_t_stack, graph_high10_type)
    return fig_high10

@app.callback(
    [Output('map-graph', 'figure'),
    Output('line-graph', 'figure'),
    Output('bar-graph', 'figure')],
    [Input('datatable', 'data'),
     Input('datatable', 'selected_rows'),
     Input('graph-line','value')])
def map_selection(data, selected_rows,graph_line):
    aux = pd.DataFrame(data)
    temp_df = aux.iloc[selected_rows, :]
    zoom = 1
    if len(selected_rows) == 0:
        fig1 = draw_singleCountry_Scatter(df_confirmed_t,df_deaths_t,df_recovered_t,0)
        fig2 = draw_singleCountry_Bar(df_confirmed_t,df_deaths_t,df_recovered_t,0,graph_line)
        return gen_map(aux,zoom,1.2833,103.8333), fig1,fig2
    else:
        fig1 = draw_singleCountry_Scatter(df_confirmed_t,df_deaths_t,df_recovered_t,selected_rows[0])
        fig2 = draw_singleCountry_Bar(df_confirmed_t,df_deaths_t,df_recovered_t,selected_rows[0],graph_line)
        zoom=4
        return gen_map(aux,zoom,temp_df['Lat'].iloc[0],temp_df['Long'].iloc[0]), fig1,fig2

# hide/show modal
@app.callback(Output('modal', 'style'),
              [Input('info-button', 'n_clicks')])
def show_modal(n):
    if n > 0:
        return {"display": "block"}
    return {"display": "none"}

# Close modal by resetting info_button click to 0
@app.callback(Output('info-button', 'n_clicks'),
              [Input('modal-close-button', 'n_clicks')])
def close_modal(n):
    return 0

if __name__ == '__main__':
    app.run_server(debug=True)
