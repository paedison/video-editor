from moviepy.editor import VideoFileClip
import numpy as np
import xml.etree.ElementTree as ET

def detect_silence(audio_clip, threshold=0.01, chunk_size=100):
    """Detect silence in audio. Returns list of silent intervals."""
    if audio_clip is None:
        raise ValueError("The video has no audio track.")

    fps = audio_clip.fps
    duration = audio_clip.duration

    silent_intervals = []
    current_time = 0

    for chunk in audio_clip.iter_chunks(fps=fps, chunksize=chunk_size):
        chunk_magnitude = np.mean(np.abs(chunk))
        if chunk_magnitude < threshold:
            silent_intervals.append((current_time, current_time + chunk_size / fps))
        current_time += chunk_size / fps

    return silent_intervals

def generate_shotcut_project(video_file, output_project_file, threshold=0.01, chunk_size=100):
    # Load the video file
    video_clip = VideoFileClip(video_file)

    if video_clip.audio is None:
        raise ValueError("The video has no audio track.")

    audio_clip = video_clip.audio

    # Detect silent sections in the audio
    silent_sections = detect_silence(audio_clip, threshold, chunk_size)

    # Find non-silent sections
    non_silent_sections = []
    current_start = 0.0

    for start, end in silent_sections:
        if current_start < start:
            non_silent_sections.append((current_start, start))  # Non-silent part
        current_start = end  # Move to the end of the current silent part

    if current_start < video_clip.duration:
        non_silent_sections.append((current_start, video_clip.duration))

    # Generate MLT XML content
    mlt = ET.Element('mlt', profile="hdv_720_25p", version="6.26.0")

    # Add the video producer (reference to original video)
    producer = ET.SubElement(mlt, 'producer', id="original_video")
    ET.SubElement(producer, 'property', name="resource").text = video_file

    # Add a playlist (list of clips)
    playlist = ET.SubElement(mlt, 'playlist', id="playlist0")

    # Insert non-silent sections into the playlist
    for i, (start, end) in enumerate(non_silent_sections):
        entry = ET.SubElement(playlist, 'entry', producer="original_video")
        ET.SubElement(entry, 'in').text = str(int(start * video_clip.fps))
        ET.SubElement(entry, 'out').text = str(int(end * video_clip.fps) - 1)

    # Add a track to define the timeline with clips
    tractor = ET.SubElement(mlt, 'tractor', id="tractor0")
    track = ET.SubElement(tractor, 'track', producer="playlist0")

    # Generate the XML tree and write it to the project file
    tree = ET.ElementTree(mlt)
    tree.write(output_project_file, encoding='utf-8', xml_declaration=True)

# Example usage
generate_shotcut_project("input_video.mp4", "output_project.mlt")
