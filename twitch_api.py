# Import
import os
import pandas as pd
import numpy as np
import json
import twitch
import requests

from datetime import datetime, timedelta
from dotenv import load_dotenv
from pytimeparse.timeparse import timeparse

load_dotenv()

CLIENT_ID = os.getenv('API_CLIENT_ID')
CLIENT_SECRET = os.getenv('API_CLIENT_SECRET')
GRANT_TYPE = os.getenv('GRANT_TYPE')

params = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': GRANT_TYPE
}

response = requests.post('https://id.twitch.tv/oauth2/token', data=params)
d = json.loads(response.text)
ACCESS_TOKEN = d['access_token']

headers = {
    'Client-ID': CLIENT_ID,
    'Authorization': 'Bearer ' + ACCESS_TOKEN
}

def dl_vod(VIDEO_ID):
    if os.path.exists("./data/" + str(VIDEO_ID) + ".json"):
        return "Done cache"
    cmd = 'tcd --client-id ' + CLIENT_ID + ' --client-secret ' + CLIENT_SECRET + ' --video ' + str(VIDEO_ID) + ' --format json --output ./data'
    os.system(cmd)
    return "Done DL"

def treatment_df(df):
    df = df[~df["message.body"].str.contains('@')]
    return df

def msg_per_minutes(df):

    msg_per_min = df[['created_at', 'content_offset_seconds']].copy()
    msg_per_min['created_at'] = pd.to_datetime(msg_per_min['created_at'])
    msg_per_min['nb_messages'] = 1

    print(msg_per_min)
    msg_per_min = msg_per_min.groupby(
            pd.Grouper(
                key='created_at', 
                freq='1min'
                ),
        ).agg({'nb_messages':'count', 
            'content_offset_seconds':'first', 
            })
    msg_per_min['date'] = msg_per_min.index
    msg_per_min['date'] = msg_per_min['date'].astype('str')
    return msg_per_min

def determine_n_best_moment(nb, df, VIDEO_ID):
    df_biggest = df.nlargest(nb, 'nb_messages')
    for index, row in df_biggest.iterrows():
        data = {
            "vod_id": VIDEO_ID,
            "offset": row['content_offset_seconds'],
        }
        res = requests.post('https://api.twitch.tv/helix/clips', data = data, headers = headers)
        print(res.text)
    return

def get_n_best_moment(n, VIDEO_ID, infos_vod):
    helix = twitch.Helix(CLIENT_ID, CLIENT_SECRET)

    url = (f'https://api.twitch.tv/helix/clips?broadcaster_id={infos_vod["user_id"]}&started_at={infos_vod["created_at_RFC"]}&ended_at={infos_vod["ended_at_RFC"]}&first={n}')
    res = requests.get(url, headers = headers)
    list_clips = json.loads(res.text)['data']

    return_list = []
    for clip in list_clips:
        print(helix.user(clip['creator_name']))
        clip['url_user_image'] = helix.user(clip['creator_name']).profile_image_url
        return_list.append(clip)
    return list_clips

def read_chat_vod(VIDEO_ID):
    with open('data/' + str(VIDEO_ID) + '.json', 'r') as f:
        data = json.load(f)
    data_normalize = pd.json_normalize(data['comments'])
    df = pd.DataFrame.from_records(data_normalize)
    print(df)
    return df

def read_info_vod(VIDEO_ID):
    helix = twitch.Helix(CLIENT_ID, CLIENT_SECRET)
    video_info = helix.video(VIDEO_ID)
    data = {}
    data['view_count'] = video_info.view_count
    data['duration'] = video_info.duration
    data['created_at_RFC'] = video_info.created_at
    video_info.created_at = datetime.fromisoformat(video_info.created_at[:-1] + '+00:00')
    data['created_at'] = video_info.created_at.date()
    data['ended_at_RFC'] = (video_info.created_at + timedelta(seconds=timeparse(data['duration']))).isoformat('T').replace('+00:00', 'Z')
    data['id'] = video_info.id
    data['user_id'] = video_info.user_id
    return data