from xml.dom import DOMException
from dash import Dash, html, dcc, Input, Output
from dash.exceptions import PreventUpdate

import datetime
import pandas as pd

import chatters
from plotly.subplots import make_subplots
import plotly.graph_objects as go
pd.options.mode.chained_assignment = None


app = Dash(__name__)
server = app.server

df = pd.read_csv('chat_data.csv')


#  Find the dates for which chat data is available
# valid_dates = set(pd.read_sql_query('SELECT DISTINCT stream_date FROM chatters', conn)['stream_date'].values)
valid_dates = set(df['stream_date'].unique())

ids = df[['stream_date', 'vod_id']].value_counts().sort_index().reset_index(name='count')

id_times = []
dupes = ids['stream_date'].duplicated()

for j in range(ids.shape[0]):
    row = df[(df['stream_date'] == ids['stream_date'].iloc[j]) & (df['vod_id'] == ids['vod_id'].iloc[j])]
    max_row = max(row['timestamp']).split(':')
    max_time = int(max_row[0]) * 3600 + int(max_row[1]) * 60 + int(max_row[2])
    id_times.append(max_time)


id_map = {ids['vod_id'].iloc[k]: [ids['stream_date'].iloc[k], id_times[k]] for k in range(ids.shape[0])}
base = datetime.datetime.strptime(max(valid_dates), '%Y-%m-%d')
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
    dcc.Store(id='data-store', storage_type='session', clear_data=True),
    dcc.DatePickerSingle(
        id='date-picker',
        min_date_allowed=start_date,
        max_date_allowed=base,
        date=base,
        disabled_days=disable
    ),
    dcc.Dropdown(
        id='phrase-show',
        multi=True
        ),
    html.Div([
        dcc.Graph(id='phrase-graph'),
    ]),
    html.A(
        children='',
        id='moon2tv-link',
    )
])


@app.callback(Output('data-store', 'data'),
              Input('date-picker', 'date'),
              prevent_initial_call=True)
def load_date(date_selected):

    #  Load the data from the dataframe for the date selected
    filtered = df[df["stream_date"] == date_selected]
    filtered.reset_index(inplace=True)
    #  Process the data
    filtered = process_data(filtered)
    # print(filtered.memory_usage(index=True, deep=True).sum())
    try:
        return filtered.to_dict('records')
    except DOMException:
        raise PreventUpdate



@app.callback(
    [
        Output('moon2tv-link', 'href'),
        Output('moon2tv-link', 'children'),
    ],
    [
        Input('phrase-graph', 'clickData'),
    ]
)
def redirect(clickData):
    if not clickData:
        raise PreventUpdate
    t_stamp_dt = clickData["points"][0]['x']
    t_date = t_stamp_dt.split(' ')[0]
    t_stamp_dt = datetime.datetime.strptime(t_stamp_dt, '%Y-%m-%d %H:%M:%S')
    tlink = t_stamp_dt.hour * 3600 + t_stamp_dt.minute * 60 + t_stamp_dt.second
    offset = 0
    for v_id, date_w_max in id_map.items():
        if t_date == date_w_max[0]:
            if tlink < date_w_max[1]:
                link = 'https://moon2.tv/youtube/'+str(v_id)+'?t='+str(tlink-offset)+'s'
                return tuple((link, link))
            else:
                offset = date_w_max[1]


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
        data = load_date(max(valid_dates))
        #  Don't break the webpage
        # raise PreventUpdate
    #  Create empty figure, to be populated later
    figure = make_subplots(specs=[[{"secondary_y": True}]])

    if not data:
        #  If there is no data (date selected has no chat data), return an empty figure
        raise PreventUpdate
        # data = load_date(max(valid_dates))
        # return tuple((figure, []))

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
    full_chat = data.resample('60S', on='timestamp').max()['allchat']
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
            y=-0.2,
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
            x=full_chat.index,
            y=full_chat.values,
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
    app.run_server(threaded=True, port=10450)
