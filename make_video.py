import os

from moviepy.editor import *
from dotenv import load_dotenv

load_dotenv()

IMAGEMAGICK_BINARY = os.getenv ('IMAGEMAGICK_BINARY', 'C:\Program Files\ImageMagick-7.0.8-Q16\convert.exe')

def concat_clips(VIDEO_ID, list_clips):
    to_concat = []
    for clip in list_clips:
        clipx = VideoFileClip(clip['path'])

        w,h = moviesize = clipx.size

        # A CLIP WITH A TEXT AND A BLACK SEMI-OPAQUE BACKGROUND
        txt = TextClip(clip['text'], font='Amiri-regular',
                        color='white',fontsize=51)

        txt_col = txt.on_color(size=(txt.w,txt.h),
                        color=(0,0,0), pos=('left','center'), col_opacity=0.6)

        f = CompositeVideoClip([clipx,txt_col.set_duration(clipx.duration)])

        to_concat.append(f)

    final = concatenate_videoclips(to_concat)
    final.write_videofile("./data/"+str(VIDEO_ID)+"/clips.mp4",temp_audiofile="./data/"+str(VIDEO_ID)+"/tmp.mp3")

    return "/"+str(VIDEO_ID)+"/clips.mp4"