from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip
import numpy as np



def resize_with_black_bars(video_clip, target_size):
    """
    Resizes a video clip to fit within the given target_size while preserving the aspect ratio.
    Black bars (letterbox or pillarbox) are added if needed.

    :param video_clip: A VideoFileClip object
    :param target_size: Tuple (width, height) of the final video
    :return: A resized VideoFileClip with black bars
    """
    # Calculate scale to fit within target size while keeping aspect ratio
    video_ratio = video_clip.w / video_clip.h
    target_ratio = target_size[0] / target_size[1]

    if video_ratio > target_ratio:
        # Video is wider than target -> fit by width
        new_width = target_size[0]
        new_height = int(target_size[0] / video_ratio)
    else:
        # Video is taller than target -> fit by height
        new_height = target_size[1]
        new_width = int(target_size[1] * video_ratio)

    # Resize video while keeping aspect ratio
    resized_video = video_clip.resize((new_width, new_height))

    # Create black background
    black_bg = ColorClip(target_size, color=(0, 0, 0), duration=video_clip.duration)

    # Center the resized video on the black background
    final_video = CompositeVideoClip([black_bg, resized_video.set_position("center")])

    return final_video

# Define movement function supporting multiple transitions
def move_overlay(t, transitions):
    for start_time, transition_duration, start_pos, end_pos in transitions:
        if start_time <= t < start_time + transition_duration:
            progress = (t - start_time) / transition_duration
            progress = 0.5 * (1 - np.cos(progress * np.pi))  # Smooth acceleration
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
            return (x, y)

    # If no transition applies, return last position
    return transitions[-1][2]  # Last end position


# List of transitions [(start_time, duration, start_pos, end_pos)]
transitions = [
    (0, 2, (0, 0), (0, 0)),
    (2, 2, (0, 0), (500, 0)),
    (4, 2, (500, 0), (500, 300)),
    (6, 2, (500, 300), (0, 300)),
    (8, 2, (0, 300), (0, 0)),
    (10, 2, (0, 0), (0, 0)),
]

# Load overlay video and apply movement
overlay_video = VideoFileClip("overlay.mp4")

# Resize while preserving aspect ratio (adds black bars if needed)
overlay_video = resize_with_black_bars(overlay_video, (100, 100))

overlay_video = overlay_video.set_position(lambda t: move_overlay(t, transitions))

background = ImageClip("background.jpg").set_duration(overlay_video.duration).resize((600, 400))

# Create composite video with layers
final_clip = CompositeVideoClip([background, overlay_video])

# Export the final video
final_clip.write_videofile("output.mp4", fps=30)
