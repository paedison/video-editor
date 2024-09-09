from moviepy.editor import VideoFileClip, concatenate_videoclips
import numpy as np


def detect_silence(audio_clip, threshold=0.01, chunk_size=100):
    """Detect silence in audio by iterating over chunks."""
    if audio_clip is None:
        raise ValueError("The video has no audio track.")

    fps = audio_clip.fps
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


def remove_silence(video_file, output_file, threshold=0.00075, chunk_size=100):
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

    # Add the last non-silent section
    if current_start < video_clip.duration:
        non_silent_sections.append((current_start, video_clip.duration))

    # Extract and concatenate non-silent video clips
    non_silent_clips = [video_clip.subclip(start, end) for start, end in non_silent_sections]

    if not non_silent_clips:
        raise ValueError("No non-silent sections were detected.")

    final_clip = concatenate_videoclips(non_silent_clips)

    # Write the result to a new video file
    final_clip.write_videofile(output_file, codec='libx264')


# Example usage
remove_silence("input_video.mp4", "output_video_no_silence.mp4")
