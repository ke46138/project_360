"""Модуль для создания диалогов в стиле Deltarune (процесс-рендерер)"""

import os
import sys
import random
import textwrap
from io import BytesIO

from PIL import ImageFont, ImageDraw, Image
import numpy as np
import moviepy.editor as moviepy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

FONT_PATH = os.path.join(ASSETS_DIR, "determination-mono.ttf")
FONT_SIZE = 25
BG_IMAGE = os.path.join(ASSETS_DIR, "deltarune-dark.png")
TYPE_SOUND = os.path.join(ASSETS_DIR, "sans.mp3")
FPS = 30
CHAR_DELAY = 0.09

def make_block(text: str, iconfile: BytesIO):
    with Image.open(BG_IMAGE).convert("RGB") as background:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        frames = []
        audio_clips = []

        for i in range(1, len(text) + 1):
            frame = background.copy()
            draw = ImageDraw.Draw(frame)
            draw.text((150, 30), text[:i], font=font, fill=(255, 255, 255))
            frames.append(np.array(frame))

            if text[i - 1] == " ":
                continue

            start_time = (i - 1) * CHAR_DELAY
            click = moviepy.AudioFileClip(TYPE_SOUND).set_start(start_time)
            click = click.set_duration(click.duration)
            audio_clips.append(click)

    clip = moviepy.ImageSequenceClip(frames, durations=[CHAR_DELAY] * len(frames))
    icon = moviepy.ImageClip(iconfile)

    last_frame = clip.to_ImageClip(t=clip.duration).set_duration(1)
    pred_final = moviepy.concatenate_videoclips([clip, last_frame])

    icon = icon.set_duration(pred_final.duration).set_position((30, 32))

    duration = len(frames) * CHAR_DELAY
    final = moviepy.CompositeVideoClip([pred_final, icon])
    typing_audio = moviepy.CompositeAudioClip(audio_clips).set_duration(duration)

    final = final.set_audio(typing_audio)
    return final

def create_dialog_task(text: str, avatar: str) -> str:
    video_blocks = []
    text_blocks = textwrap.wrap(text, width=90)

    avatar_resized_pil = Image.open(avatar)
    avatar_resized_pil = avatar_resized_pil.resize((105, 105), Image.LANCZOS)
    avatar_resized = BytesIO()
    avatar_resized_pil.save(avatar_resized, format='PNG')
    avatar_resized.seek(0)

    img_data = avatar_resized.getvalue()

    for j in text_blocks:
        wrapped_text = textwrap.wrap(j, width=28)
        block_text = f"* {'\n  '.join(wrapped_text)}"
        video_blocks.append(make_block(block_text, BytesIO(img_data)))

    clip = moviepy.concatenate_videoclips(video_blocks)
    temp_path = os.path.join('/tmp', f"bot-{random.randint(1000, 9999999)}.mp4")
    clip.write_videofile(temp_path, codec="libx264", audio_codec="aac", fps=FPS, verbose=False, logger=None)
    clip.close()

    return temp_path

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        avatar_file = sys.argv[1]
        dialog_text = sys.argv[2]
        print(f"--------PATH: {create_dialog_task(dialog_text, avatar_file)}", end="")
