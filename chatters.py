import datetime
import math
import re
import pandas as pd
from scipy.signal import find_peaks


#  Split chat messages into the smallest base unit. This helps the chat density accurately reflect copy-pasted messages.
#  eg One row in the dataframe: "NODDERS Clap NODDERS Clap NODDERS Clap NODDERS Clap"
#  becomes four rows of "NODDERS Clap" with the same timestamps
def parse_logs(data):
    all_chat = []
    all_times = []
    all_density = []
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
        all_density.extend([data.loc[i, 'allchat']]*pasta_len)
        all_chat.extend([msg_no_pasta]*pasta_len)
        all_times.extend([data.loc[i, 'dt_combo']]*pasta_len)
    alldf = pd.DataFrame(list(zip(all_times, all_chat, all_density)), columns=['timestamp', 'message', 'allchat'])
    return alldf


def full_density(chatlog, window):
    # Calculate the density of all chat messages sent. This uses the raw data input and not the result of "parse_logs()" above
    w = str(window)+'s'  # Currently disabled, may re-enable to allow users to adjust the summation window? Probably not
    chatlog['allchat'] = chatlog['message'].str.replace('.*', '1', regex=True, n=1)
    chatlog.set_index(chatlog['dt_combo'], inplace=True)
    chatlog.drop(['index'], inplace=True, axis=1)
    # Calculate rolling sum of all messages sent within last 15 seconds
    chatlog['allchat'] = chatlog['allchat'].rolling(window=datetime.timedelta(seconds=15)).sum()
    chatlog = chatlog.reset_index(drop=True)
    return chatlog


def find_phrases(chatlog):
    # Trim the dataframe to exclude messages only sent one time.
    # This prevents the dataframe from exceeding the window local storage limit (5 MB)
    # Typically this reduces the number of rows by about half
    # (Note: about 95% of the original chat file is removed, meaning that 5% of all messages are repeated about half the time LOL)
    phrases = chatlog['message'].value_counts()
    phrases = phrases[phrases > 5]  # Adjust this parameter to exclude more data.
    # A value of '1' means that messages that are only sent once are removed.
    chatlog = chatlog.loc[chatlog['message'].isin(phrases.index)]
    chatlog.reset_index(inplace=True, drop=True)
    return chatlog


#  Calculate the density of a specific emote or phrase in chat
#  This uses the result from "parse_logs()" above
def phrase_density(chatlog, phrases, searchtype, window):
    w = str(window)+'s'  # Currently disabled, may re-enable to allow users to adjust the summation window?
    searchtype = str(searchtype).lower()
    conc = pd.DataFrame()
    #  For each emote/phrase, add a column to the dataframe
    for emote in phrases:
        conc[emote] = chatlog[searchtype].str.contains(re.escape(emote), flags=re.IGNORECASE)
    conc.set_index(chatlog['timestamp'], inplace=True)
    #  Calculate the 15-second rolling sum on each column to get the density
    conc = conc.rolling(window=datetime.timedelta(seconds=15)).sum()
    conc = conc.fillna(0)
    conc.reset_index(inplace=True)
    #  Calculate the peak values (highest density) of each emote using scipy's "find_peaks()"
    peak_phrases = []
    peak_values = []
    peak_heights = []
    for e in range(len(phrases)):
        peaks = find_peaks(conc[phrases[e]], distance=2000, height=10)  # These parameters can be changed to increase/decrease number of "highlighted" points
        for p in range(len(peaks[0])):
            peak_y = peaks[1]['peak_heights'][p]
            peak_x = chatlog['timestamp'].iloc[peaks[0][p]]
            peak_phrases.append(phrases[e])
            peak_values.append(peak_x)
            peak_heights.append(peak_y)
    peak_val = pd.DataFrame({'phrase': peak_phrases, 'count': peak_heights}, index=peak_values)
    peak_val.sort_index(inplace=True)
    return {
        'peak_val': peak_val,
        'density': conc}
