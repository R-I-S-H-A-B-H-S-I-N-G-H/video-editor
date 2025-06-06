from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip,concatenate
import numpy as np
import json

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


# Define scale transition function
def scale_overlay(t, scale_transitions):
    for start_time, duration, start_scale, end_scale in scale_transitions:
        if start_time <= t < start_time + duration:
            progress = (t - start_time) / duration
            progress = 0.5 * (1 - np.cos(progress * np.pi))  # Smooth easing
            scale = start_scale + (end_scale - start_scale) * progress
            return scale
    return scale_transitions[-1][2]  # Return last end scale if no transition applies

def resize_overlay(t, resize_transitions):
    for start_time, duration, start_size, end_size in resize_transitions:
        if start_time <= t < start_time + duration:
            progress = (t - start_time) / duration
            progress = 0.5 * (1 - np.cos(progress * np.pi))  # Smooth easing

            w = start_size[0] + (end_size[0] - start_size[0]) * progress
            h = start_size[1] + (end_size[1] - start_size[1]) * progress
            return (w, h)
    return resize_transitions[-1][2]  # Last known size

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

def generateLayer(config):
    output_video_path = config["output_video"]
    layersConfArr = config["layers"]
    layers = []

    for layerConf in layersConfArr:
        file_type = layerConf.get("type")
        size = layerConf.get("size")
        path = layerConf.get("path")
        duration = layerConf.get("duration")
        
        transitionsConf = layerConf.get("transitions", [])
        
        layerClip = None
        if file_type == "image":
            layerClip = ImageClip(path).resize(size).set_duration(duration)
        if file_type == "video":
            layerClip = VideoFileClip(path)
            layerClip = layerClip.resize(size)

        for transitionConf in transitionsConf:
            transition_type = transitionConf.get("type")
            keyFramesConf = transitionConf.get("keyFrames", [])

            if transition_type == "position":
                transitions_list = []
                for keyFrameConf in keyFramesConf:
                    start_time = keyFrameConf.get("start")
                    duration = keyFrameConf.get("dur")
                    start_pos = keyFrameConf.get("startPos")
                    end_pos = keyFrameConf.get("endPos")
                    transitions_list.append((start_time, duration, start_pos, end_pos))

                if transitions_list:
                    layerClip = layerClip.set_position(lambda t, p_trans = transitions_list: move_overlay(t, p_trans))
            
            
            if transition_type == "scale":
                print('SCALE')
                resize_transitions = []
                for keyFrameConf in keyFramesConf:
                    start_time = keyFrameConf.get("start", 0)
                    duration = keyFrameConf.get("dur", 1)
                    start_size = keyFrameConf.get("startSize")
                    end_size = keyFrameConf.get("endSize")
                    resize_transitions.append((start_time, duration, start_size, end_size))

                if resize_transitions:
                    layerClip = layerClip.resize(lambda t, r_trans=resize_transitions: resize_overlay(t, r_trans))

        if layerClip:
            layers.append(layerClip)

    final_clip = CompositeVideoClip(layers)
    final_clip.write_videofile(output_video_path, fps=30)


def readJson(path):
    with open(path, "r") as file:
        config = json.load(file)
        return config


config = readJson("config.json")
generateLayer(config=config)
