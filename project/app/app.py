from dash import Dash, html, dcc, Input, Output
from dash.exceptions import PreventUpdate
import datetime
import pandas as pd
import sqlite3
import chatters
from plotly.subplots import make_subplots
import plotly.graph_objects as go
pd.options.mode.chained_assignment = None


app = Dash(__name__)
server = app.server
#  Connect to the local database

# conn = sqlite3.connect('../data/chat_data.db', check_same_thread=False)
# c = conn.cursor()

#  Load in the entire database, to be filtered later
# df = pd.read_sql_query("SELECT * FROM chatters", conn)
# df.to_csv('../data/chat_data.csv', index=False)

df = pd.read_csv('chat_data.csv')

#  Find the dates for which chat data is available
# valid_dates = set(pd.read_sql_query('SELECT DISTINCT stream_date FROM chatters', conn)['stream_date'].values)
valid_dates = set(df['stream_date'].unique())

base = datetime.datetime.today()
start_date = datetime.datetime.strptime(min(valid_dates), '%Y-%m-%d')
numdays = (base - start_date).days
date_list = set((base - datetime.timedelta(days=x)).strftime('%Y-%m-%d') for x in range(numdays))
disable_dates = date_list - valid_dates
#  Return a list of dates to be disabled for selection in the HTML SingleDatePicker
disable = [datetime.datetime.strptime(y, '%Y-%m-%d') for y in disable_dates]


def process_data(data):
    #  Create a column with both date and time (stored separately in the database)
    data['dt_combo'] = pd.to_datetime(data['stream_date'].apply(str) + ' ' + data['timestamp'])
    #  Calculate the density of all messages sent
    chatfile = chatters.full_density(data, window=15)
    #  Split message data to account for copy+pasted messages with repeated phrases
    chatfile = chatters.parse_logs(chatfile)
    #  Trim the dataset, remove phrases/messages that are repeated less than 5 times
    chatfile = chatters.find_phrases(chatfile)
    return chatfile


app.layout = html.Div([
    dcc.Store(id='data-store', storage_type='session'),
    dcc.DatePickerSingle(
        id='date-picker',
        min_date_allowed=start_date,
        max_date_allowed=datetime.date.today() - datetime.timedelta(days=1),
        date=max(valid_dates),
        disabled_days=disable
    ),
    dcc.Dropdown(
        id='phrase-show',
        multi=True
        ),
    html.Div([
        dcc.Graph(id='phrase-graph'),
    ])
])


@app.callback(Output('data-store', 'data'),
              Input('date-picker', 'date'))
def load_date(date_selected):
    #  Load the data from the dataframe for the date selected
    filtered = df[df["stream_date"] == date_selected]
    filtered.reset_index(inplace=True)
    #  Process the data
    filtered = process_data(filtered)
    # print("num rows= ", filtered.shape[0])
    # print("file size=", filtered.memory_usage(index=True, deep=True).sum()/1000000)
    return filtered.to_dict('records')


@app.callback(
    [
        Output('phrase-graph', 'figure'),
        Output('phrase-show', 'options'),
    ],
    [
        Input('data-store', 'data'),
        Input('phrase-show', 'value'),
    ]
)
def on_data_set_graph(data, field):
    if data is None:
        #  Don't break the webpage
        raise PreventUpdate
    #  Create empty figure, to be populated later
    figure = make_subplots(specs=[[{"secondary_y": True}]])

    if not data:
        #  If there is no data (date selected has no chat data), return an empty figure
        return tuple((figure, []))

    data = pd.DataFrame(data)
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    #  Find the top used emotes/phrases in the chat
    top_phrases = data['message'].value_counts().index.tolist()
    if not field:
        #  If no emotes/phrases have been selected from the dropdown, display the top 5 emotes/phrases
        phrases_to_show = top_phrases[:5]
    elif len(field) == 1:
        #  Do this to prevent parsing the dropdown value as a string, rather than item in list
        phrases_to_show = field
    else:
        phrases_to_show = field
    #  Calculate the density of the selected emotes/phrases
    processed_chat = chatters.phrase_density(data, phrases_to_show, searchtype='message', window=datetime.timedelta(seconds=15))
    peaks = processed_chat['peak_val']
    density = processed_chat['density']

    figure.update_xaxes(
        nticks=20,
        tick0=0,
        tickformat="%H:%M:%S"
    )
    figure.update_layout(
        title='Emote Usage, {w:.2s} Second Rolling Sum'.format(w=str(15)),
        xaxis_title='Timestamp (HH:MM:SS)',
        legend=dict(
            orientation='h',
            y=-0.3,
        ),
    )
    figure.update_yaxes(
        title_text='Selected Usage in {w:.2s}s'.format(w=str(15)),
        secondary_y=False
    )
    figure.update_yaxes(
        title_text='Total Chat messages in {w:.2s}s'.format(w=str(15)),
        secondary_y=True
    )
    for e in phrases_to_show:
        peak_x = peaks[peaks['phrase'] == e].index.tolist()
        peak_y = peaks[peaks['phrase'] == e]['count']
        figure.add_trace(
            go.Scatter(
                x=density['timestamp'],
                y=density[e],
                name=e,
                hoverinfo='none',
                mode='lines',
            ),
            secondary_y=False,

        )
        figure.add_trace(
            go.Scatter(
                showlegend=False,
                x=peak_x,
                y=peak_y,
                name=e,
                hoverinfo='x+name',
                mode='markers',
                fillcolor='purple',
                marker=dict(
                    color='black'
                ),
            ),
            secondary_y=False,
        )
    figure.add_trace(
        go.Scatter(
            x=data['timestamp'].values,
            y=data['allchat'].values,
            dx=1000*60*10,
            name="All Chat Messages",
            hoverinfo='none',
            hovertext='none',
            legendrank=1,
            line=dict(
                color='rgba(0, 0, 0, 0.7)',
                width=0.2)
        ),
        secondary_y=True,
    )

    return tuple((figure, top_phrases))


if __name__ == '__main__':
    app.run_server(debug=True, threaded=True, port=10450)
