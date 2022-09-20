import pandas as pd
import re
import sqlite3


def main(vod_id):
    conn = sqlite3.connect('project/data/chat_data.db')
    connection = conn.cursor()
    connection.execute('CREATE TABLE IF NOT EXISTS chatters (stream_date date, timestamp text, username text, message text)')
    conn.commit()
    log_path = 'G:/MOONMOON/highlights/'+str(vod_id)+'/source/'+str(vod_id)+'.log'
    with open(log_path, 'r', encoding="utf8") as chat_file:
        chat = chat_file.read().splitlines()
    date = chat[0].split('T')[0]
    date = [date]*len(chat)
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

        tstamps.append(t)
        users.append(u)
        msg.append(c)

    df = pd.DataFrame(list(zip(date, tstamps, users, msg)), columns=['stream_date', 'timestamp', 'username', 'message'])
    df.to_sql('chatters', conn, if_exists='append', index=False)


if __name__ == "__main__":
    main(1591900038)
