#
# Animation Script v5.0
# Inspired by Deforum Notebook
# Must have ffmpeg installed in path.
# Poor img2img implentation, will trash images that aren't moving.
#
# See https://github.com/Animator-Anon/Animator
import json
import os
import time

import gradio as gr

from scripts.functions import prepwork, sequential, loopback, export
from modules import script_callbacks
from modules import shared, sd_models


def myprocess(_steps, _sampler_index, _width, _height, _cfg_scale, _denoising_strength, _total_time, _fps,
              _smoothing, _add_noise, _noise_strength, _seed, _seed_travel, _initial_img,
              _loopback_mode, _prompt_interpolation, _tmpl_pos, _tmpl_neg,
              _key_frames, _vid_gif, _vid_mp4, _vid_webm, _style_pos, _style_neg):
    # Build a dict of the settings, so we can easily pass to sub functions.
    myset = {'steps': int(_steps),
             'sampler_index': int(_sampler_index),
             'width': int(_width),
             'height': int(_height),
             'cfg_scale': float(_cfg_scale),
             'denoising_strength': float(_denoising_strength),
             'total_time': float(_total_time),
             'fps': float(_fps),
             'key_frames': str(_key_frames).strip(),
             'vid_gif': bool(_vid_gif),
             'vid_mp4': bool(_vid_mp4),
             'vid_webm': bool(_vid_webm),
             'seed': int(_seed),
             'seed_travel': bool(_seed_travel),
             'prompt_interpolation': bool(_prompt_interpolation),
             'add_noise': _add_noise,
             'smoothing': int(_smoothing),
             'tmpl_pos': str(_tmpl_pos).strip(),
             'tmpl_neg': str(_tmpl_neg).strip(),
             '_style_pos': str(_style_pos).strip(),
             '_style_neg': str(_style_neg).strip(),
             'noise_strength': float(_noise_strength),
             'loopback': bool(_loopback_mode),
             'source': ""}

    # Sort out output folder
    if len(shared.opts.animatoranon_output_folder.strip())> 0:
        output_parent_folder = shared.opts.animatoranon_output_folder.strip()
    elif myset['loopback']:
        output_parent_folder = shared.opts.outdir_img2img_samples
    else:
        output_parent_folder = shared.opts.outdir_samples
    output_parent_folder = os.path.join(output_parent_folder, time.strftime('%Y%m%d%H%M%S'))
    if not os.path.exists(output_parent_folder):
        os.makedirs(output_parent_folder)
    myset['output_path'] = output_parent_folder

    # Save the parameters to a file.
    settings_filename = os.path.join(myset['output_path'], "settings.txt")
    with open(settings_filename, "w+", encoding="utf-8") as f:
        json.dump(myset, f, ensure_ascii=False, indent=4)

    # Have to add the initial picture later on as it doesn't serialise well.
    myset['initial_img'] = _initial_img

    # Prepare the processing objects with default values.
    ptxt, pimg = prepwork.setup_processors(myset)

    # Make bat files before video incase we interrupt it, and so we can generate vids on the fly.
    export.make_batch_files(myset)

    shared.state.interrupted = False
    if myset['loopback']:
        result = loopback.main_process(myset, ptxt, pimg)
    else:
        result = sequential.main_process(myset, ptxt)

    if not shared.state.interrupted:
        # Generation not cancelled, go ahead and render the videos without stalling.
        export.make_videos(myset)

    return result


def ui_block_generation():
    with gr.Blocks():
        with gr.Accordion("Generation Parameters", open=False):
            gr.HTML("<p>These parameters mirror those in txt2img and img2img mode. They are used "
                    "to create the initial image in loopback mode.</p>")
        steps = gr.Slider(minimum=1, maximum=150, step=1, label="Sampling Steps", value=20)
        from modules.sd_samplers import samplers_for_img2img
        sampler_index = gr.Radio(label='Sampling method',
                                 choices=[x.name for x in samplers_for_img2img],
                                 value=samplers_for_img2img[0].name, type="index")

        with gr.Group():
            with gr.Row():
                width = gr.Slider(minimum=64, maximum=2048, step=64, label="Width", value=512)
                height = gr.Slider(minimum=64, maximum=2048, step=64, label="Height", value=512)
        with gr.Group():
            with gr.Row():
                cfg_scale = gr.Slider(minimum=1.0, maximum=30.0, step=0.5, label='CFG Scale', value=7.0)
                denoising_strength = gr.Slider(minimum=0.0, maximum=1.0, step=0.01,
                                               label='Denoising strength', value=0.40)
        with gr.Row():
            seed = gr.Number(label='Seed', value=-1)
            seed_travel = gr.Checkbox(label='Seed Travel', value=False)

        with gr.Row():
            with gr.Accordion("Initial Image", open=False):
                initial_img = gr.inputs.Image(label = 'Upload starting image',
                                              image_mode ='RGB',
                                              type='pil',
                                              optional=True)

    return steps, sampler_index, width, height, cfg_scale, denoising_strength, seed, seed_travel, initial_img


def ui_block_animation():
    with gr.Blocks():
        with gr.Accordion("Animation Parameters", open=False):
            gr.HTML("Parameters for the animation. Total length in seconds will determine the length of"
                    " the animation.<br>"
                    "<ul>"
                    "<li>Total Animation Length: How long the resulting animation will be. Total number "
                    "of frames rendered will be this time * FPS</li> "
                    "<li>Smoothing Frames: The number of additional intermediate frames to insert between "
                    "every rendered frame. These will be a faded merge of the surrounding frames.</li> "
                    "<li>Add Noise: Add simple noise to the image in the form of random coloured circles. "
                    "These can help the loopback mode create new content.</li> "
                    "<li>Loopback: This is the img2img loopback mode where the resulting image, "
                    "before post processing, is pre-processed and fed back in..</li> "
                    "<li>Prop Folder: Path to folder containing transparent .png files that can be "
                    "superimposed in pre or post processing.</li> "
                    "</ul>")
        with gr.Row():
            total_time = gr.Number(label="Total Animation Length (s)", lines=1, value=10.0)
            fps = gr.Number(label="Framerate", lines=1, value=15.0)
            smoothing = gr.Slider(label="Smoothing_Frames", minimum=0, maximum=32, step=1, value=0)
        with gr.Row():
            add_noise = gr.Checkbox(label="Add_Noise", value=False)
            noise_strength = gr.Slider(label="Noise Strength", minimum=0.0, maximum=1.0, step=0.01,
                                       value=0.10)
        with gr.Row():
            loopback_mode = gr.Checkbox(label='Loopback Mode', value=True)

    return total_time, fps, smoothing, add_noise, noise_strength, loopback_mode


def ui_block_processing():
    with gr.Blocks():
        with gr.Accordion("Prompt Template, applied to each keyframe below", open=False):
            gr.HTML("<p>Prompt interpolation will set both before and after prompts with a weighting that linearly "
                    "grows from the current prompt to the next.<br>"
                    "Similar to styles, these prompt templates are applied to every frame in addition to the"
                    " keyframe / VTT prompts below.</p>")
        prompt_interpolation = gr.Checkbox(label='Prompt Interpolation', value=True)
        with gr.Row():
            tmpl_pos = gr.Textbox(label="Positive Prompts", lines=1, value="")
            style_pos = gr.Dropdown(label="Use pos prompts from style",
                                    choices=[k for k, v in shared.prompt_styles.styles.items()],
                                    value=next(iter(shared.prompt_styles.styles.keys())))
        with gr.Row():
            tmpl_neg = gr.Textbox(label="Negative Prompts", lines=1, value="")
            style_neg = gr.Dropdown(label="Use neg prompts from style",
                                    choices=[k for k, v in shared.prompt_styles.styles.items()],
                                    value=next(iter(shared.prompt_styles.styles.keys())))

    return prompt_interpolation, tmpl_pos, style_pos, tmpl_neg, style_neg


def ui_block_keyframes():
    with gr.Blocks():
        with gr.Accordion("Supported Keyframes:", open=False):
            gr.HTML("Copy and paste these templates, replace values as required.<br>"
                    "time_s | source | video, images, img2img | path<br>"
                    "time_s | prompt | positive_prompts | negative_prompts<br>"
                    "time_s | template | positive_prompts | negative_prompts<br>"
                    "time_s | prompt_from_png | file_path<br>"
                    "time_s | prompt_vtt | vtt_filepath<br>"
                    "time_s | seed | new_seed_int<br>"
                    "time_s | denoise | denoise_value<br>"
                    "time_s | cfg_scale | cfg_scale_value<br>"
                    "time_s | transform | zoom | x_shift | y_shift | rotation<br>"
                    "time_s | noise | added_noise_strength<br>"
                    "time_s | set_text | textblock_name | text_prompt | x_pos | y_pos | width | height | fore_color |"
                    " back_color | font_name<br> "
                    "time_s | clear_text | textblock_name<br>"
                    "time_s | prop | prop_filename | x_pos | y_pos | scale | rotation<br>"
                    "time_s | set_stamp | stamp_name | stamp_filename | x_pos | y_pos | scale | rotation<br>"
                    "time_s | clear_stamp | stamp_name<br>"
                    "time_s | col_set<br>"
                    "time_s | col_clear<br>"
                    "time_s | model | " + ", ".join(
                                                    sorted(
                                                        [x.model_name for x in sd_models.checkpoints_list.values()]
                                                    )) + "</p>")

        return gr.Textbox(label="Keyframes:", lines=5, value="")


def ui_block_settings():
    with gr.Blocks():
        gr.HTML("Persistent settings moved into the main settings tab, in the group <b>Animator Extension</b>")


def ui_block_output():
    with gr.Blocks():
        with gr.Accordion("Output Block", open=False):
            gr.HTML("<p>Video creation options. Check the formats you want automatically created."
                    "Otherwise manually execute the batch files in the output folder.</p>")

        with gr.Row():
            vid_gif = gr.Checkbox(label="GIF", value=False)
            vid_mp4 = gr.Checkbox(label="MP4", value=False)
            vid_webm = gr.Checkbox(label="WEBM", value=True)

        gallery = gr.Gallery(label="gallery", show_label=True).style(grid=5, height="auto")

        with gr.Row():
            btn_proc = gr.Button(value="Process")
            btn_stop = gr.Button(value='Stop')

    return vid_gif, vid_mp4, vid_webm, gallery, btn_proc, btn_stop


#
# Basic layout of page
#
def on_ui_tabs():

    with gr.Blocks(analytics_enabled=False) as animator_tabs:
        with gr.Row():
            # left Column
            with gr.Column():
                with gr.Tab("Generation"):
                    steps, sampler_index, width, height, cfg_scale, denoising_strength, seed, seed_travel, image_list =\
                        ui_block_generation()

                    total_time, fps, smoothing, add_noise, noise_strength, loopback_mode = ui_block_animation()

                    prompt_interpolation, tmpl_pos, style_pos, tmpl_neg, style_neg = ui_block_processing()

                    key_frames = ui_block_keyframes()

                with gr.Tab("Persistent Settings"):
                    ui_block_settings()

            # Right Column
            with gr.Column():
                vid_gif, vid_mp4, vid_webm, gallery, btn_proc, btn_stop = ui_block_output()

            btn_proc.click(fn=myprocess,
                           inputs=[steps, sampler_index, width, height, cfg_scale, denoising_strength, total_time,
                                   fps, smoothing, add_noise, noise_strength, seed, seed_travel, image_list,
                                   loopback_mode, prompt_interpolation,
                                   tmpl_pos, tmpl_neg, key_frames, vid_gif, vid_mp4, vid_webm, style_pos, style_neg],
                           outputs=gallery)

            btn_stop.click(
                fn=lambda: shared.state.interrupt(),
                inputs=[],
                outputs=[],
            )

    return (animator_tabs, "Animator", "animator"),


#
# Define my options that will be stored in webui config
#
def on_ui_settings():

    mysection = ('animatoranon', 'Animator Extension')

    shared.opts.add_option("animatoranon_film_folder",
                           shared.OptionInfo('c:/ai/film',
                                             label="FILM folder (contains predict.py)",
                                             section=mysection))
    shared.opts.add_option("animatoranon_prop_folder",
                           shared.OptionInfo('c:/ai/props',
                                             label="Prop folder",
                                             section=mysection))
    shared.opts.add_option("animatoranon_output_folder",
                           shared.OptionInfo('',
                                             label="New output folder",
                                             section=mysection))



script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_ui_settings(on_ui_settings)
