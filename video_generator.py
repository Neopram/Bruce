# video_generator.py

import os
import uuid
import json
import datetime
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from gtts import gTTS
from typing import Optional, List


class VideoConfig:
    """
    âš™ï¸ ConfiguraciÃ³n base para los clips de Bruce.
    """
    def __init__(self, resolution=(1280, 720), fps=30, font="Arial", fontsize=50, color="white"):
        self.resolution = resolution
        self.fps = fps
        self.font = font
        self.fontsize = fontsize
        self.color = color


class SceneBlock:
    """
    ðŸ§  Representa una escena modular dentro del clip cognitivo generado por Bruce.
    """
    def __init__(self, text: str, duration: float = 5.0, tts_language: str = "en"):
        self.id = str(uuid.uuid4())
        self.text = text
        self.duration = duration
        self.tts_language = tts_language
        self.audio_path = None

    def generate_audio(self, output_dir: str = "temp/audio"):
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{self.id}.mp3"
        self.audio_path = os.path.join(output_dir, filename)
        tts = gTTS(self.text, lang=self.tts_language)
        tts.save(self.audio_path)


class BruceVideoGenerator:
    """
    ðŸŽ¬ MÃ³dulo de Bruce para generar videos con overlays inteligentes, audio TTS y narrativa simbiÃ³tica.
    """
    def __init__(self, config: VideoConfig = VideoConfig(), output_dir="output/videos"):
        self.config = config
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_clip_from_block(self, block: SceneBlock) -> CompositeVideoClip:
        block.generate_audio()

        text_clip = TextClip(
            block.text,
            fontsize=self.config.fontsize,
            font=self.config.font,
            color=self.config.color,
            size=self.config.resolution,
            method='caption'
        ).set_duration(block.duration)

        audio_clip = AudioFileClip(block.audio_path).subclip(0, block.duration)
        text_clip = text_clip.set_audio(audio_clip)

        return text_clip

    def generate_full_video(self, blocks: List[SceneBlock], title: Optional[str] = None) -> str:
        clips = [self.generate_clip_from_block(block) for block in blocks]
        final_clip = concatenate_videoclips(clips, method="compose")

        if title:
            filename = f"{title.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        else:
            filename = f"bruce_clip_{uuid.uuid4().hex}.mp4"

        output_path = os.path.join(self.output_dir, filename)
        final_clip.write_videofile(output_path, fps=self.config.fps)

        return output_path

    def generate_from_script(self, script: str, language: str = "en") -> str:
        """
        ðŸš€ Divide un script largo en bloques, genera audio, video y exporta.
        """
        sentences = script.split(". ")
        blocks = [SceneBlock(text=s.strip() + ".", tts_language=language) for s in sentences if s.strip()]
        return self.generate_full_video(blocks, title="bruce_script")

    def export_metadata(self, video_path: str, blocks: List[SceneBlock]):
        metadata = {
            "video_path": video_path,
            "generated": datetime.datetime.utcnow().isoformat() + "Z",
            "blocks": [
                {
                    "id": b.id,
                    "text": b.text,
                    "duration": b.duration,
                    "audio": b.audio_path
                } for b in blocks
            ]
        }
        metadata_path = video_path.replace(".mp4", "_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

