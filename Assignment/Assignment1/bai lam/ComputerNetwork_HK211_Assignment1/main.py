import subprocess


def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return float(result.stdout)


def with_opencv(filename):
    import cv2
    video = cv2.VideoCapture(filename)

    duration = video.get(cv2.CAP_PROP_POS_MSEC)
    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)

    return duration, frame_count


def with_ffprobe(filename):
    import subprocess, json

    result = subprocess.check_output(
        f'ffprobe -v quiet -show_streams -select_streams v:0 -of json "{filename}"',
        shell=True).decode()
    fields = json.loads(result)['streams'][0]

    duration = fields['tags']['DURATION']
    fps = eval(fields['r_frame_rate'])
    return duration, fps


def with_moviepy(filename):
    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(filename)
    duration = clip.duration
    fps = clip.fps
    width, height = clip.size
    return duration, fps, (width, height)


print(with_opencv('movie.Mjpeg'))
