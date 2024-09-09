from moviepy.editor import *
import numpy as np


def detect_silence(audio_clip, threshold=-40.0, chunk_size=1000, merge_threshold=1):
    fps = audio_clip.fps
    duration = audio_clip.duration

    audio_array = audio_clip.to_soundarray(fps=fps)
    audio_volume = 20 * np.log10(np.maximum(np.abs(audio_array), 1e-10))  # Avoid log of zero

    silent_sections = []
    current_start = None

    for i in range(0, len(audio_volume), chunk_size):
        avg_volume = np.mean(audio_volume[i:i + chunk_size])
        t = i / fps

        if avg_volume < threshold:  # Silence
            if current_start is not None:
                silent_sections.append((current_start, t))
                current_start = None
        else:  # Non-silent
            if current_start is None:
                current_start = t

    # Append any remaining non-silent section
    if current_start is not None:
        silent_sections.append((current_start, duration))

    # Merge adjacent non-silent sections based on merge_threshold
    merged_sections = []
    if silent_sections:
        current_start, current_end = silent_sections[0]

        for start, end in silent_sections[1:]:
            if start - current_end <= merge_threshold:  # Merge adjacent sections
                current_end = end
            else:
                merged_sections.append((current_start, current_end))
                current_start, current_end = start, end

        # Add the last merged section
        merged_sections.append((current_start, current_end))

    return merged_sections


def remove_silence(input_video, output_video, threshold=-40.0, chunk_size=1000, merge_threshold=1):
    video_clip = VideoFileClip(input_video)
    audio_clip = video_clip.audio
    non_silent_sections = detect_silence(audio_clip, threshold, chunk_size, merge_threshold)

    # Create subclips of non-silent sections and concatenate them
    subclips = [video_clip.subclip(start, end) for start, end in non_silent_sections]
    final_clip = concatenate_videoclips(subclips)

    final_clip.write_videofile(output_video, codec="libx264")


# Example usage
remove_silence("input_video.mp4", "output_video_no_silence.mp4", threshold=-40.0, chunk_size=1000, merge_threshold=1.0)
