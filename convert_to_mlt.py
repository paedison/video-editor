import xml.etree.ElementTree as ET
from moviepy.editor import VideoFileClip, AudioFileClip
import numpy as np


def detect_silence_0(audio_clip, threshold=0.00075, chunk_size=100):
    """ Detect silence in audio. Returns list of silent intervals. """
    if audio_clip is None:
        raise ValueError("The video has no audio track.")

    fps = audio_clip.fps
    chunks = np.array_split(audio_clip.to_soundarray(), len(audio_clip) * fps // chunk_size)
    silent_intervals = []
    for i, chunk in enumerate(chunks):
        chunk_magnitude = np.mean(np.abs(chunk))
        if chunk_magnitude < threshold:
            silent_intervals.append((i * chunk_size / fps, (i + 1) * chunk_size / fps))
    return silent_intervals


def detect_silence(audio_clip, threshold=0.01, chunk_size=500):
    """ Detect silence in audio. Returns list of silent intervals. """
    if audio_clip is None:
        raise ValueError("The video has no audio track.")

    fps = audio_clip.fps  # Frames per second of audio
    duration = audio_clip.duration

    # Initialize empty list to track silent sections
    silent_intervals = []
    current_time = 0

    for chunk in audio_clip.iter_chunks(fps=fps, chunksize=chunk_size):
        chunk_magnitude = np.mean(np.abs(chunk))
        if chunk_magnitude < threshold:
            silent_intervals.append((current_time, current_time + chunk_size / fps))
        current_time += chunk_size / fps

    return silent_intervals


def create_mlt_project(silent_sections, input_video, output_mlt):
    root = ET.Element("mlt")
    playlist = ET.SubElement(root, "playlist", id="main_playlist")

    # Add clips to playlist (skipping silent sections)
    for i, (start, end) in enumerate(silent_sections):
        clip = ET.SubElement(playlist, "entry")
        clip.set("in", str(int(start * 1000)))  # Shotcut expects times in milliseconds
        clip.set("out", str(int(end * 1000)))
        clip.set("filename", input_video)

    # Write MLT XML to file
    tree = ET.ElementTree(root)
    tree.write(output_mlt)


# Load video and extract audio
video = VideoFileClip("input_video.mp4")
audio = video.audio
silent_sections = detect_silence(audio)
create_mlt_project(silent_sections, "input_video.mp4", "output_project.mlt")
