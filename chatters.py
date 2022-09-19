import argparse
import datetime
import math

import re
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from matplotlib import cm, pyplot as plt
from scipy.signal import find_peaks
import os
global conc, allchat

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", required=True, help='Enter the path the the .log file with the twitch chat logs \n'
                                                        'To get twitch logs, visit https://github.com/PetterKraabol/Twitch-Chat-Downloader'
                                                        'and run `tcd --video [twitch-vod-id] --format irc --output ./[output_path]')
parser.add_argument("-p", "--phrase", nargs='*', default=[], required=False, help='Enter the phrase(s) to search for. For multiple phrases, enter as a list separated by a comma. If left blank, the top 20 phrases will be calculated and used instead.')
parser.add_argument("-o", "--output", default=None, required=False, help='If you want to export the chat logs to csv, enter the path to export')
parser.add_argument("-st", "--searchtype", default="message", required=False, help="Use kwarg `USERNAME` to find messages by user(s). Default is message")
parser.add_argument("-w", "--window", default='15', required=False, help="Enter a number of seconds to calculate the rolling sum within. Default is 15 seconds.")
parser.add_argument("-n", "--number", default=15, required=False, help="View the n-most used phrases")


def parse_logs(data):
    # with open(file, 'r', encoding="utf8") as chat_file:
    #     chat = chat_file.read().splitlines()
    # date = chat[0]
    # chat = chat[1:]

    all_chat = []
    all_times = []
    msg_col = data.columns.tolist().index('message')
    for i in range(data.shape[0]):
        msg = data.iloc[i, msg_col]
        msg_no_pasta = msg
        pasta_len = 1
        if len(msg.split()) > 1:
            split_msg = msg.split()
            for j in range(math.ceil(len(msg.split())/2)):
                if split_msg[0:j+1] == split_msg[j+1:2*(j+1)]:
                    msg_no_pasta = ' '.join(split_msg[0:j+1])
                    pasta_len = math.ceil(len(msg.split())/(j+1))
                    break

        all_chat.extend([msg_no_pasta]*pasta_len)
        all_times.extend([data.loc[i, 'dt_combo']]*pasta_len)
    alldf = pd.DataFrame(list(zip(all_times, all_chat)), columns=['timestamp', 'message'])

    # for msg in chat:
    #     msg = msg[1:]
    #     msg = msg.split('] <', maxsplit=1)
    #     text = msg[-1].split('> ', maxsplit=1)[-1]
    #     msg[-1] = msg[-1].split('> ')[0]
    #     msg.append(text)
    #     msg[1] = msg[1].replace('%', '')
    #     msg_no_pasta = msg[-1]
    #     pasta_len = 1
    #     if len(msg[-1].split()) > 1:
    #         split_msg = msg[-1].split()
    #         for i in range(math.ceil(len(msg[-1].split())/2)):
    #             if split_msg[0:i+1] == split_msg[i+1:2*(i+1)]:
    #                 msg_no_pasta = ' '.join(split_msg[0:i+1])
    #                 pasta_len = math.ceil(len(msg[-1].split())/(i+1))
    #                 break
    #
    #     all_chat.extend([msg_no_pasta]*pasta_len)
    #     all_times.extend([msg[0]]*pasta_len)
    #     chat_df.append(msg)

    # alldf = pd.DataFrame(list(zip(all_times, all_chat)), columns=['timestamp', 'message'])

    # alldf['timestamp'] = pd.to_datetime(alldf['timestamp'])
    #
    # alldf.set_index(alldf['timestamp'], inplace=True)

    # df = pd.DataFrame(chat_df, columns=['timestamp', 'username', 'message'])
    # df['timestamp'] = pd.to_datetime(df['timestamp'])
    # df.set_index(df['timestamp'], inplace=True)
    # df['total'] = df['message'].notna()

    # return df, alldf['message'].unique().tolist(), alldf
    # return df, alldf
    return alldf


def find_phrases(chatlog):
    # Trim the dataframe to exclude messages only sent one time.
    phrases = chatlog['message'].value_counts()
    phrases = phrases[phrases > 5]  # Adjust this parameter to exclude more data
    chatlog = chatlog.loc[chatlog['message'].isin(phrases.index)]
    chatlog.reset_index(inplace=True, drop=True)
    return chatlog


def full_density(chatlog, window):
    w = str(window)+'s'
    chatlog['allchat'] = chatlog['message'].str.replace('.*', '1', regex=True, n=1)
    chatlog.set_index(chatlog['timestamp'], inplace=True)
    chatlog['allchat'] = chatlog['allchat'].rolling(window=datetime.timedelta(seconds=15)).sum()
    chatlog = chatlog.reset_index(drop=True)

    return chatlog


def phrase_density(chatlog, phrases, searchtype, window):
    w = str(window)+'s'
    searchtype = str(searchtype).lower()
    conc = pd.DataFrame()

    for emote in phrases:
        conc[emote] = chatlog[searchtype].str.contains(re.escape(emote), flags=re.IGNORECASE)

    conc.set_index(chatlog['timestamp'], inplace=True)
    # pd.to_datetime(conc.index)

    conc = conc.rolling(window=datetime.timedelta(seconds=15)).sum()
    conc = conc.fillna(0)
    conc.reset_index(inplace=True)
    peak_phrases = []
    peak_values = []
    peak_heights = []
    # fig, ax1 = plt.subplots()
    # ax2 = ax1.twinx()

    color = cm.turbo(np.linspace(0, 1, len(phrases) + 1))
    for e in range(len(phrases)):
        peaks = find_peaks(conc[phrases[e]], distance=2000, height=10)

        # conc[phrases[e]].plot(color=color[e], ax=ax1, label=phrases[e])
        for p in range(len(peaks[0])):
            peak_y = peaks[1]['peak_heights'][p]
            peak_x = chatlog['timestamp'].iloc[peaks[0][p]]
            peak_phrases.append(phrases[e])
            peak_values.append(peak_x)
            peak_heights.append(peak_y)

            # ax1.text(peak_x[p], peak_y[p] + 1, str(peak_x[p]),
            #          color=color[e], horizontalalignment='center', path_effects=[pe.withStroke(linewidth=4, foreground="white")])

    peak_val = pd.DataFrame({'phrase': peak_phrases, 'count': peak_heights}, index=peak_values)
    # allchat.plot(color='black', alpha=0.7, ax=ax2, linewidth=0.2)
    # plt.show()
    peak_val.sort_index(inplace=True)

    # ax1.legend(loc='center left', bbox_to_anchor=(1.05, 0.5))
    # ax2.get_legend().remove()
    # ax1.set_title('MOONMOON 9/9/2022 Stream: \n Selected Emote Usage \n {w:.2s} Second Message Count Totals'.format(w=window))
    # ax1.set_ylabel('Phrase Usage in {w:.2s} Seconds'.format(w=window))
    # ax2.set_ylabel('Total Messages Sent in {w:.2s} Seconds'.format(w=window), loc='top')
    # plt.show()
    return {
        'peak_val': peak_val,
        'density': conc}


if __name__ == '__main__':
    app = Dash(__name__)
    args = parser.parse_args()
    logs, chatfile = parse_logs(args.file)
    if args.phrase:
        peaks, density, fullchat, top_phrases = find_phrases(logs, chatfile, args.phrase, args.searchtype, args.window, int(args.number))
    else:
        peaks, density, fullchat, top_phrases = find_phrases(logs, chatfile, None, args.searchtype, args.window, int(args.number))

    @app.callback(Output('phrase-graph', 'figure'),
                  Input('phrase-show', 'value'), prevent_initial_call=True)
    def build_graph(value):
        if len(value) == 0 or len(value) > 50:
            value = top_phrases[:5]
        figure = make_subplots(specs=[[{"secondary_y": True}]])
        # figure.update_xaxes(dtick='10min')
        color = px.colors.n_colors((0, 0, 0), (255, 150, 250), len(top_phrases))

        lno = 0
        for e in value:
            peak_x = peaks[peaks['phrase'] == e].index
            peak_y = peaks[peaks['phrase'] == e]['count']

            figure.add_trace(
                go.Scatter(
                    x=density.index,
                    y=density[e],
                    dx=1000*60*10,
                    name=e,
                    hoverinfo='none',
                    mode='lines',
                    # marker=dict(
                    #     color=color[lno]
                    # ),
                ),
                secondary_y=False,

            )
            figure.add_trace(
                go.Scatter(
                    showlegend=False,
                    x=peak_x,
                    y=peak_y,
                    dx=1000*60*10,
                    name=e,
                    hoverinfo='x+name',
                    mode='markers',
                    fillcolor='purple',
                    marker=dict(
                        color='black'
                    ),
                    # hoverlabel=dict(
                    #     font=dict(
                    #         color='black'
                    #         )
                    #     )
                ),
                secondary_y=False,
            )
            lno += 1
        figure.add_trace(
            go.Scatter(
                x=fullchat.index,
                y=fullchat['message'],
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
        return figure

    fig = build_graph(top_phrases)
    plot(fig, top_phrases)
    app.run_server()
    vod_id = os.path.basename(args.file).split('.')[0]
    baselink_twitch = 'https://www.twitch.tv/videos/' + vod_id + '?t='
    baselink_yt = 'https://moon2.tv/youtube/' + vod_id + '?t='
    phrases['ytlink'] = baselink_yt + (phrases['timelink']-17).astype(str) + 's'
    phrases['twitchlink'] = baselink_twitch + (phrases['timelink']-17).astype(str) + 's'
    phrases.drop('timelink', axis=1, inplace=True)
    if args.output is not None:
        Path("./output/"+vod_id).mkdir(parents=True, exist_ok=True)
        phrases.to_csv(args.output+'/'+vod_id+'/links.csv')
        logs.drop('total', axis=1, inplace=True)
        logs['timestamp'] = logs['timestamp'].dt.time
        logs.to_csv(args.output+'/'+vod_id+'/chatlog.csv', index=False)


#  TODO: add auto-generation of instances with super high chat concentration (> std * 12)
#  TODO: better copy-pasta handling (need to make df with all substrings of message?)
