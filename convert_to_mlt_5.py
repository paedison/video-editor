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

    # # Merge adjacent silent intervals based on merge_threshold
    # merged_silent_intervals = []
    # if silent_intervals:
    #     start, end = silent_intervals[0]
    #     for next_start, next_end in silent_intervals[1:]:
    #         if next_start - end <= merge_threshold:
    #             end = next_end
    #         else:
    #             merged_silent_intervals.append((start, end))
    #             start, end = next_start, next_end
    #     merged_silent_intervals.append((start, end))
    #
    # return merged_silent_intervals


def calculate_non_silent_sections(silent_intervals, total_duration):
    """Calculate non-silent sections from silent intervals."""
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


def remove_silence(input_video, output_file, threshold=0.01, chunk_size=100, merge_threshold=1.0):
    """Detect silence, calculate non-silent sections, and save as an MLT project."""
    video_clip = VideoFileClip(input_video)
    audio_clip = video_clip.audio
    total_duration = video_clip.duration

    silent_intervals = detect_silence(audio_clip, threshold, chunk_size, merge_threshold)
    non_silent_sections = calculate_non_silent_sections(silent_intervals, total_duration)

    # Prepare MLT entries
    entries = []
    for start, end in non_silent_sections:
        in_time = seconds_to_timecode(start)
        out_time = seconds_to_timecode(end)
        entries.append(f'<entry producer="chain1" in="{in_time}" out="{out_time}"/>')

    # Write to the MLT project file
    with open(output_file, 'w') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<mlt profile="hdv_720_25p" version="7.4.0">\n')
        f.write('<producer id="original_video">\n')
        f.write(f'    <property name="resource">{input_video}</property>\n')
        f.write('    <property name="mlt_service">avformat</property>\n')
        f.write('    <property name="seekable">1</property>\n')
        f.write('</producer>\n')
        f.write('<playlist id="playlist0">\n')

        for entry in entries:
            f.write(f'    {entry}\n')

        f.write('</playlist>\n')
        f.write('</mlt>\n')


# Example usage
remove_silence("input_video.mp4", "output_project.mlt", threshold=0.00075, chunk_size=100, merge_threshold=1.0)
