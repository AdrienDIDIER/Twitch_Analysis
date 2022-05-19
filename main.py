import os
import twitch
import pytz
import twitch_api

from datetime import datetime
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()

local_tz = pytz.timezone('Europe/Paris')

# Twitch
CLIENT_ID = os.getenv('API_CLIENT_ID')
CLIENT_SECRET = os.getenv('API_CLIENT_SECRET')
helix = twitch.Helix(CLIENT_ID, CLIENT_SECRET)

# API
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
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

    list_vods.append(vod)

  return templates.TemplateResponse("list_vods.html", {"request": request, "list_vods": list_vods})

@app.post("/vod", response_class=HTMLResponse)
async def home(request: Request, vod_id: int = Form()):
  infos_vod = twitch_api.read_info_vod(vod_id)
  twitch_api.dl_vod(vod_id)
  df = twitch_api.read_chat_vod(vod_id)
  df_t = twitch_api.treatment_df(df)
  df_v = twitch_api.msg_per_minutes(df_t)

  infos_chart = {
    'labels' : df_v['date'].tolist(),
    'data' : df_v['nb_messages'].tolist()
  }

  data = {}
  data['infos_vod'] = infos_vod
  data['infos_chart'] = infos_chart

  print(data)
  return templates.TemplateResponse("vod.html", {"request": request, "vod_data": data})