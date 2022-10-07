import datetime
import glob
import os.path
import shutil
import pandas as pd
import re
import sqlite3


def main(path):
    conn = sqlite3.connect('G:/MOONMOON/moonlights_data/chat_data.db')
    connection = conn.cursor()
    connection.execute('CREATE TABLE IF NOT EXISTS chatters (stream_date date, vod_id number, timestamp text, username text, message text)')
    conn.commit()
    connection.execute("SELECT DISTINCT stream_date FROM chatters")
    all_dates = connection.fetchall()
    all_dates = [all_dates[i][0] for i in range(len(all_dates))]
    with open(path, 'r', encoding="utf8") as chat_file:
        chat = chat_file.read().splitlines()
    date = chat[0].split('T')[0]
    vid = os.path.basename(path).split('.')[0]
    t_offset = 0
    if date in all_dates:
        connection.execute(f"SELECT timestamp FROM chatters WHERE stream_date IS '{date}' ORDER BY timestamp DESC LIMIT 1")
        t_offset = connection.fetchall()[0][0]
        t_offset = t_offset.split(':')
        t_offset = datetime.timedelta(hours=int(t_offset[0]), minutes=int(t_offset[1]), seconds=int(t_offset[2]))
    date = [date]*len(chat)
    vid = [vid] * len(chat)
    badges = ['!', '$', '~', '*', '@', '+', '&', '%']
    tstamps = []
    users = []
    msg = []
    chat.pop(0)

    for c in chat:
        t = re.search(r'\A\[(.*?)\]', c).group(1)
        c = c.removeprefix('['+t+'] ')
        badge = c[1]
        u = re.search(r'\A<(.*?)>', c).group(1)
        if badge in badges:
            u = u[1:]
            c = c.removeprefix('<'+badge+u+'> ')
        else:
            c = c.removeprefix('<'+u+'> ')
        if t_offset != 0:
            t = datetime.datetime.strptime(t, '%H:%M:%S').time()
            t = (datetime.datetime.combine(datetime.date(1, 1, 1), t) + t_offset)
            t = datetime.datetime.strftime(t, '%H:%M:%S')
        tstamps.append(t)
        users.append(u)
        msg.append(c)
    df = pd.DataFrame(list(zip(date, vid, tstamps, users, msg)), columns=['stream_date', 'vod_id', 'timestamp', 'username', 'message'])
    df.to_sql('chatters', conn, if_exists='append', index=False)
    fulldf = pd.read_sql_query("SELECT * FROM chatters", conn)
    fulldf.to_csv('D:/IdeaProjects/PyCharm/yt-transcribe/project/app/chat_data.csv')



if __name__ == "__main__":
    # RUN tcd --video ######### --format irc --output G:/MOONMOON/highlights/source/
    vid_number = 1611164207
    file = f"G:/MOONMOON/highlights/source/{vid_number}.log"
    main(file)
    shutil.copyfile('G:/MOONMOON/moonlights_data/chat_data.db', 'D:/IdeaProjects/PyCharm/yt-transcribe/project/app/chat_data.db')

    exit()
    # for file in glob.iglob("G:/MOONMOON/highlights/source/*"):
    #     main(file)
