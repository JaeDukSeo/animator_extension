import os
import subprocess


def make_batch_files(myset: dict):
    final_fps = myset['fps'] + myset['fps'] * myset['smoothing']
    make_gif(myset['output_path'], 'video', final_fps, False, True)
    make_mp4(myset['output_path'], 'video', final_fps, False, True)
    make_webm(myset['output_path'], 'video', final_fps, False, True)


def make_videos(myset: dict):
    final_fps = myset['fps'] + myset['fps'] * myset['smoothing']
    make_gif(myset['output_path'], 'video', final_fps, myset['vid_gif'], False)
    make_mp4(myset['output_path'], 'video', final_fps, myset['vid_mp4'], False)
    make_webm(myset['output_path'], 'video', final_fps, myset['vid_webm'], False)


def make_gif(filepath: str, filename: str, fps: float, create_vid: bool, create_bat: bool):
    # Create filenames
    in_filename = f"frame_%05d.png"
    out_filename = f"{str(filename)}.gif"
    # Build cmd for bat output, local file refs only
    cmd = [
        'ffmpeg',
        '-y',
        '-r', str(fps),
        '-i', in_filename.replace("%", "%%"),
        out_filename
    ]
    # create bat file
    if create_bat:
        with open(os.path.join(filepath, "makegif.bat"), "w+", encoding="utf-8") as f:
            f.writelines([" ".join(cmd)])
            # f.writelines([" ".join(cmd), "\r\n", "pause"])
    # Fix paths for normal output
    cmd[5] = os.path.join(filepath, in_filename)
    cmd[6] = os.path.join(filepath, out_filename)
    # create output if requested
    if create_vid:
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def make_webm(filepath: str, filename: str, fps: float, create_vid: bool, create_bat: bool):
    in_filename = f"frame_%05d.png"
    out_filename = f"{str(filename)}.webm"

    cmd = [
        'ffmpeg',
        '-y',
        '-framerate', str(fps),
        '-i', in_filename.replace("%", "%%"),
        '-crf', str(50),
        '-preset', 'veryfast',
        out_filename
    ]

    if create_bat:
        with open(os.path.join(filepath, "makewebm.bat"), "w+", encoding="utf-8") as f:
            f.writelines([" ".join(cmd)])
            # f.writelines([" ".join(cmd), "\r\n", "pause"])

    cmd[5] = os.path.join(filepath, in_filename)
    cmd[10] = os.path.join(filepath, out_filename)

    if create_vid:
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def make_mp4(filepath: str, filename: str, fps: float, create_vid: bool, create_bat: bool):
    in_filename = f"frame_%05d.png"
    out_filename = f"{str(filename)}.mp4"

    cmd = [
        'ffmpeg',
        '-y',
        '-r', str(fps),
        '-i', in_filename.replace("%", "%%"),
        '-c:v', 'libx264',
        '-vf',
        f'fps={fps}',
        '-pix_fmt', 'yuv420p',
        '-crf', '17',
        '-preset', 'veryfast',
        out_filename
    ]

    if create_bat:
        with open(os.path.join(filepath, "makemp4.bat"), "w+", encoding="utf-8") as f:
            f.writelines([" ".join(cmd)])
            # f.writelines([" ".join(cmd), "\r\n", "pause"])

    cmd[5] = os.path.join(filepath, in_filename)
    cmd[16] = os.path.join(filepath, out_filename)

    if create_vid:
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
