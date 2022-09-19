import datetime
import math
import re
from scipy.signal import find_peaks
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.patheffects as pe
import plotly.express as px
import plotly.graph_objects as go

''' run `tcd --video [twitch-vod-id] --format irc --output ./output'''

with open('./output/1586576070.log', 'r', encoding="utf8") as chat_file:
    chat = chat_file.read().splitlines()

chat_df = []

for msg in chat:
    msg = msg[1:]
    msg = msg.split('] <', maxsplit=1)
    text = msg[-1].split('> ', maxsplit=1)[-1]
    msg[-1] = msg[-1].split('> ')[0]
    msg.append(text)
    msg[1] = msg[1].replace('%', '')
    chat_df.append(msg)

df = pd.DataFrame(chat_df, columns=['timestamp', 'username', 'message'])
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index(df['timestamp'], inplace=True)
df['total'] = df['message'].notna()

# exit()
# df.to_csv('./output/test1.csv')
moments = ['OMEGALAUGHING', 'DESKCHAN', 'PEPW', 'POGPLANT', 'cum', 'borpa', 'stare', 'NaM', 'OBA DOBA', 'BOOBA', 'BALD',
           'Corpa', 'DOCING', 'ayayaJAM', 'modCheck', 'TAUNTED', 'BOOMIES', 'NOOO', 'GIGA', 'OF HELL', 'Wokege',
           'Bedge', 'sadge', 'monkaGIGA', 'moon2spin']

while True:
    fig = go.Figure()
    conc = pd.DataFrame()
    # emotes = str(input("Enter keyword(s) or emote(s), separated by commas: ")).split(', ')
    emotes = moments

    for emote in emotes:
        conc[emote] = df['message'].str.contains(emote, flags=re.IGNORECASE)

    conc = conc.rolling(window='30s').sum()
    conc = conc[conc[emotes] > conc[emotes].std() * 3]
    conc['timestamp'] = conc.index
    conc['timestamp'] = conc['timestamp'].dt.time
    conc.set_index(conc['timestamp'], inplace=True)
    conc = conc.fillna(0)
    # conc.drop('timestamp', inplace=True, axis=1)

    color = cm.rainbow(np.linspace(0, 1, len(emotes) + 1))
    for e in range(len(emotes)):
        peaks = find_peaks(conc[emotes[e]], distance=3000)
        peak_y = conc[emotes[e]].iloc[peaks[0]]

        #  This code is used to generate more dynamic Plotly figures. It is good for looking at a lot of data at once,
        #  but runs more slowly than the matplotlib code

        # fig.add_trace(go.Scatter(
        #     x=conc['timestamp'],
        #     y=conc[emotes[e]],
        #     mode='lines',
        #     name=emotes[e]
        # ))
        #
        # fig.add_trace(go.Scatter(
        #     x=conc['timestamp'].iloc[peaks[0]],
        #     y=peak_y.values,
        #     text=conc['timestamp'].iloc[peaks[0]],
        #     mode='text',
        #     name=emotes[e]+' Key moments',
        #     textposition='top center'
        # ))

        conc[emotes[e]].plot(color=color[e])
        for p in range(len(peaks[0])):
            plt.text(conc['timestamp'].iloc[peaks[0][p]], peak_y[p] + 1, str(conc['timestamp'].iloc[peaks[0][p]]),
                     color=color[e], horizontalalignment='center', path_effects=[pe.withStroke(linewidth=4, foreground="white")])


    plt.legend()
    plt.title('MOONMOON 9/9/2022 Stream: \n Selected Emote Usage \n 30-Second Message Count Totals')
    plt.ylabel('usage')
    plt.show()
    # fig.show()  # show plotly figure

