import os
import twitch
import pytz
import twitch_api

from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from pytimeparse.timeparse import timeparse

load_dotenv()

local_tz = pytz.timezone('Europe/Paris')

# Twitch
CLIENT_ID = os.getenv('API_CLIENT_ID')
CLIENT_SECRET = os.getenv('API_CLIENT_SECRET')
helix = twitch.Helix(CLIENT_ID, CLIENT_SECRET)

# API
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
  return templates.TemplateResponse("home.html", {"request": request})


@app.post("/list/", response_class=HTMLResponse)
async def get_vod_streamer(request: Request, name: str = Form()):
  
  list_vods = []
  for video in helix.user(name).videos():
    video.created_at = datetime.fromisoformat(video.created_at[:-1] + '+00:00')
    video.created_at = video.created_at.date()

    if "https" in video.thumbnail_url:
      video.thumbnail_url = video.thumbnail_url.replace("""%{width}""", """218""").replace("""%{height}""", """120""")
    else:
      video.thumbnail_url = None
  
    vod = {
      "id" : video.id,
      "title" : video.title,
      "created_at" : video.created_at,
      "thumbnail_url" : video.thumbnail_url,
      "duration" : video.duration,
      "url" : video.url
      }

    if video.type == 'archive':
      list_vods.append(vod)

  return templates.TemplateResponse("list_vods.html", {"request": request, "list_vods": list_vods})

@app.post("/vod", response_class=HTMLResponse,)
async def vod(request: Request, background_tasks: BackgroundTasks, vod_id: int = Form(), vod_old_id: int = Form()):
  infos_vod = twitch_api.read_info_vod(vod_id)
  old_infos_vod = twitch_api.read_info_vod(vod_old_id)

  twitch_api.dl_vod(vod_id)
  df = twitch_api.read_chat_vod(vod_id)

  df_t = twitch_api.treatment_df(df)
  df_v = twitch_api.msg_per_minutes(df_t)
  # test = twitch_api.determine_n_best_moment(5, df_v, vod_id)
  list_clips, url_mounted = twitch_api.get_n_best_moment(5, vod_id, infos_vod, background_tasks)

  infos_chart = {
    'labels' : df_v['date'].tolist(),
    'nb_messages' : df_v['nb_messages'].tolist(),
    'content_offset_seconds' : df_v['content_offset_seconds'].tolist()
  }
  
  s1 = timeparse(infos_vod['duration'])
  s2 = timeparse(old_infos_vod['duration'])
 
  time_1 = timedelta(seconds=s1)
  time_2 = timedelta(seconds=s2)

  data = {}
  data['infos_vod'] = infos_vod
  data['evol'] = {
    'evol_view_count' : round(((float(infos_vod['view_count']) - float(old_infos_vod['view_count']))/float(old_infos_vod['view_count']))*100,2),
    'evol_duration' : round(((time_1 - time_2)/time_2)*100,2),
  }
  data['infos_chart'] = infos_chart
  return templates.TemplateResponse("vod.html", {"request": request, "vod_data": data, "list_clips": list_clips, "url_mounted": url_mounted})
