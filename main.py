from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip, concatenate
import numpy as np
import json

def move_overlay(t, transitions):
    # Default to the first position if t is before all transitions
    last_pos = transitions[0][2]  # Start with first start_pos
    
    for start_time, transition_duration, start_pos, end_pos in transitions:
        if start_time <= t < start_time + transition_duration:
            progress = (t - start_time) / transition_duration
            progress = 0.5 * (1 - np.cos(progress * np.pi))  # Smooth easing
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
            return (x, y)
        elif t >= start_time + transition_duration:
            last_pos = end_pos  # Update last position after transition completes
    
    return last_pos  # Return last known position if beyond all transitions

def scale_overlay(t, scale_transitions):
    last_scale = scale_transitions[0][2]  # Start with first start_scale
    
    for start_time, duration, start_scale, end_scale in scale_transitions:
        if start_time <= t < start_time + duration:
            progress = (t - start_time) / duration
            progress = 0.5 * (1 - np.cos(progress * np.pi))
            return start_scale + (end_scale - start_scale) * progress
        elif t >= start_time + duration:
            last_scale = end_scale
    
    return last_scale

def generateLayer(config):
    output_video_path = config["output_video"]
    layersConfArr = config["layers"]
    layers = []

    for layer_idx, layerConf in enumerate(layersConfArr):
        file_type = layerConf.get("type")
        size = layerConf.get("size")
        path = layerConf.get("path")
        duration = layerConf.get("duration")
        transitionsConf = layerConf.get("transitions", [])
        
        # Create the base clip
        if file_type == "image":
            layerClip = ImageClip(path).resize(size).set_duration(duration)
        elif file_type == "video":
            layerClip = VideoFileClip(path).resize(size)
            if duration:
                layerClip = layerClip.set_duration(duration)

        layerClip = layerClip.set_start(0)

        # Apply transitions
        for transitionConf in transitionsConf:
            transition_type = transitionConf.get("type")
            keyFramesConf = transitionConf.get("keyFrames", [])

            if transition_type == "position":
                if keyFramesConf:
                    # Create a copy of transitions specific to this layer
                    transitions_list = [(kf.get("start"), kf.get("dur"), kf.get("startPos"), kf.get("endPos")) 
                                      for kf in keyFramesConf]
                    # Bind the transitions to this specific layer's movement
                    layerClip = layerClip.set_position(lambda t, tl=transitions_list: move_overlay(t, tl))

            if transition_type == "scale":
                if keyFramesConf:
                    scale_transitions = [(kf.get("start", 0), kf.get("dur", 1), 
                                        kf.get("startScale", 1.0), kf.get("endScale", 1.0)) 
                                       for kf in keyFramesConf]
                    layerClip = layerClip.resize(lambda t, st=scale_transitions: scale_overlay(t, st))

        if layerClip:
            layers.append(layerClip.set_opacity(1))
            # Debug print to verify initial position
            print(f"Layer {layer_idx} ({path}) initial pos: {layerClip.pos(0)}")

    # Use background size for composite
    final_clip = CompositeVideoClip(layers, size=layers[0].size)
    final_clip.write_videofile(output_video_path, fps=30, codec='libx264', audio=False)

def readJson(path):
    with open(path, "r") as file:
        return json.load(file)

config = readJson("config.json")
generateLayer(config=config)