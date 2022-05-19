# Import
import os
import pandas as pd
import numpy as np
import json
import twitch

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('API_CLIENT_ID')
CLIENT_SECRET = os.getenv('API_CLIENT_SECRET')

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

def read_chat_vod(VIDEO_ID):
    with open('data/' + str(VIDEO_ID) + '.json', 'r') as f:
        data = json.load(f)
    data_normalize = pd.json_normalize(data['comments'])
    df = pd.DataFrame.from_records(data_normalize)
    return df

def read_info_vod(VIDEO_ID):
    helix = twitch.Helix(CLIENT_ID, CLIENT_SECRET)
    video_info = helix.video(VIDEO_ID)
    data = {}
    data['view_count'] = video_info.view_count
    data['duration'] = video_info.duration
    video_info.created_at = datetime.fromisoformat(video_info.created_at[:-1] + '+00:00')
    video_info.created_at = video_info.created_at.date()
    data['created_at'] = video_info.created_at
    data['id'] = video_info.id
    return data