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


def generate_shotcut_project_with_clips(video_file, output_project_file, threshold=0.00075, chunk_size=100):
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

    # Create the root of the MLT XML tree
    mlt = ET.Element('mlt', profile="hdv_720_25p", version="7.4.0")  # Updated version for compatibility

    # Add the original video as a producer (reference the video file)
    producer = ET.SubElement(mlt, 'producer', id="original_video")
    ET.SubElement(producer, 'property', name="resource").text = video_file
    ET.SubElement(producer, 'property', name="mlt_service").text = "avformat"
    ET.SubElement(producer, 'property', name="seekable").text = "1"

    # Create a playlist for the video clips
    playlist = ET.SubElement(mlt, 'playlist', id="playlist0")

    # Add non-silent sections of the video to the playlist
    for i, (start, end) in enumerate(non_silent_sections):
        entry = ET.SubElement(playlist, 'entry', producer="original_video")
        in_time = int(start * video_clip.fps)
        out_time = int(end * video_clip.fps) - 1
        if out_time < in_time:
            out_time = in_time  # Ensure no negative durations

        ET.SubElement(entry, 'in').text = str(in_time)
        ET.SubElement(entry, 'out').text = str(out_time)

    # Add a tractor to define the timeline (reference the playlist)
    tractor = ET.SubElement(mlt, 'tractor', id="tractor0")
    ET.SubElement(tractor, 'property', name="shotcut").text = "1"
    ET.SubElement(tractor, 'track', producer="playlist0")
    ET.SubElement(tractor, 'transition', mlt_service="mix", in_track="0", out_track="1", a_track="0", b_track="1")

    # Write the XML tree to the output file
    tree = ET.ElementTree(mlt)
    tree.write(output_project_file, encoding='utf-8', xml_declaration=True)

# Example usage
generate_shotcut_project_with_clips("input_video.mp4", "output_project_with_clips.mlt")
