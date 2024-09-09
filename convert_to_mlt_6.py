from moviepy.editor import *
import numpy as np
from datetime import timedelta


def seconds_to_timecode(seconds):
    """Convert seconds to 'hh:mm:ss.SSS' format."""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    return f"{str(td).split('.')[0]}.{milliseconds:03d}"


def detect_silence(audio_clip, threshold=0.01, chunk_size=100, merge_threshold=1.0):
    """Detect silence in audio and return a list of silent intervals."""
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

    # Merge adjacent silent intervals based on merge_threshold
    merged_silent_intervals = []
    if silent_intervals:
        start, end = silent_intervals[0]
        for next_start, next_end in silent_intervals[1:]:
            if next_start - end <= merge_threshold:
                end = next_end
            else:
                merged_silent_intervals.append((start, end))
                start, end = next_start, next_end
        merged_silent_intervals.append((start, end))

    return merged_silent_intervals


def calculate_non_silent_sections(silent_intervals, total_duration):
    """Calculate non-silent (voiced) sections from silent intervals."""
    non_silent_sections = []
    current_start = 0

    for start, end in silent_intervals:
        if current_start < start:
            non_silent_sections.append((current_start, start))
        current_start = end

    # Add final non-silent section if there is time left
    if current_start < total_duration:
        non_silent_sections.append((current_start, total_duration))

    return non_silent_sections


def create_mlt_project_with_tracks(input_video, output_file, voiced_sections):
    """Generate an MLT project with voiced sections displayed on a track."""
    # Prepare MLT entries
    entries = []
    for i, (start, end) in enumerate(voiced_sections, 1):
        in_time = seconds_to_timecode(start)
        out_time = seconds_to_timecode(end)
        chain_id = f"chain{i}"
        entries.append(f'<entry producer="{chain_id}" in="{in_time}" out="{out_time}"/>')

    # Write the MLT project file
    with open(output_file, 'w') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<mlt profile="hdv_720_25p" version="7.4.0">\n')

        # Define the original video as a producer
        f.write('<producer id="original_video">\n')
        f.write(f'    <property name="resource">{input_video}</property>\n')
        f.write('    <property name="mlt_service">avformat</property>\n')
        f.write('    <property name="seekable">1</property>\n')
        f.write('</producer>\n')

        # Create chains for each voiced section (each sound section becomes its own producer)
        for i, (start, end) in enumerate(voiced_sections, 1):
            in_time = seconds_to_timecode(start)
            out_time = seconds_to_timecode(end)
            chain_id = f"chain{i}"
            f.write(f'<producer id="{chain_id}">\n')
            f.write(f'    <property name="resource">{input_video}</property>\n')
            f.write(f'    <property name="in">{in_time}</property>\n')
            f.write(f'    <property name="out">{out_time}</property>\n')
            f.write('</producer>\n')

        # Add all the entries to a playlist
        f.write('<playlist id="playlist0">\n')
        for entry in entries:
            f.write(f'    {entry}\n')
        f.write('</playlist>\n')

        # Track section
        f.write('<tractor id="tractor0">\n')
        f.write('    <multitrack>\n')
        f.write('        <track producer="playlist0"/>\n')  # All voiced sections on a track
        f.write('    </multitrack>\n')
        f.write('</tractor>\n')

        f.write('</mlt>\n')


def remove_silence(input_video, output_file, threshold=0.01, chunk_size=100, merge_threshold=1.0):
    """Detect silence, calculate voiced sections, and save as an MLT project."""
    video_clip = VideoFileClip(input_video)
    audio_clip = video_clip.audio
    total_duration = video_clip.duration

    silent_intervals = detect_silence(audio_clip, threshold, chunk_size, merge_threshold)
    voiced_sections = calculate_non_silent_sections(silent_intervals, total_duration)

    create_mlt_project_with_tracks(input_video, output_file, voiced_sections)


# Example usage
remove_silence("input_video.mp4", "output_project_with_tracks.mlt", threshold=0.01, chunk_size=100, merge_threshold=1.0)
