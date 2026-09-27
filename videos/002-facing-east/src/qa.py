"""Automated QA for the final video (writes build/qa/).

- ffprobe stream summary (codec, profile, pix_fmt, size, fps, bitrate, durations)
- frames every 2 s + one frame per narration line at full visibility, as contact sheets
- blackdetect / freezedetect scans
- EBU R128 loudness + true peak of the muxed audio
- subtitle file matches the on-screen narration exactly
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.abspath(os.path.join(HERE, ".."))
QA = os.path.join(VID, "build", "qa")
FINAL = os.path.join(VID, "output", "final_video.mp4")
sys.path.insert(0, HERE)
import story  # noqa: E402

TOOLS = os.path.abspath(os.path.join(VID, "..", "..", "tools"))


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    os.makedirs(os.path.join(QA, "frames"), exist_ok=True)
    os.makedirs(os.path.join(QA, "lines"), exist_ok=True)
    report = []
    pr = sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", FINAL])
    info = json.loads(pr.stdout)
    for s in info["streams"]:
        if s["codec_type"] == "video":
            report.append(f"video: {s['codec_name']} {s.get('profile')} {s['pix_fmt']} "
                          f"{s['width']}x{s['height']} {s['r_frame_rate']} fps "
                          f"{int(s.get('bit_rate', 0)) / 1e6:.1f} Mbps dur {s['duration']}s "
                          f"frames {s.get('nb_frames')}")
        else:
            report.append(f"audio: {s['codec_name']} {s['sample_rate']} Hz {s['channels']} ch "
                          f"{int(s.get('bit_rate', 0)) / 1e3:.0f} kbps dur {s['duration']}s")
    report.append(f"container duration {float(info['format']['duration']):.3f}s, "
                  f"overall {int(info['format']['bit_rate']) / 1e6:.1f} Mbps")

    # frames every 2 s
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", FINAL, "-vf", "fps=1/2,scale=640:-1",
        os.path.join(QA, "frames", "f_%03d.png")])
    frames = sorted(os.listdir(os.path.join(QA, "frames")))
    for k in range(0, len(frames), 12):
        chunk = [os.path.join(QA, "frames", f) for f in frames[k:k + 12]]
        sh([sys.executable, os.path.join(TOOLS, "contact_sheet.py"),
            os.path.join(QA, f"sheet_{k // 12:02d}.png"), "4", "480"] + chunk)
    # every narration line at the middle of its fully-visible hold
    for i, (s, e, txt) in enumerate(story.LINES, 1):
        mid = (s + e) / 2
        sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{mid:.3f}", "-i", FINAL,
            "-frames:v", "1", "-vf", "crop=1920:300:0:780",
            os.path.join(QA, "lines", f"line_{i:02d}.png")])
    lines = sorted(os.listdir(os.path.join(QA, "lines")))
    for k in range(0, len(lines), 10):
        chunk = [os.path.join(QA, "lines", f) for f in lines[k:k + 10]]
        sh([sys.executable, os.path.join(TOOLS, "contact_sheet.py"),
            os.path.join(QA, f"lines_{k // 10}.png"), "1", "1400"] + chunk)

    bd = sh(["ffmpeg", "-i", FINAL, "-vf", "blackdetect=d=0.25:pic_th=0.97:pix_th=0.06",
             "-an", "-f", "null", "-"]).stderr
    blacks = re.findall(r"black_start:(\S+) black_end:(\S+)", bd)
    report.append(f"black segments (>=0.25 s): {blacks or 'none'}")
    fz = sh(["ffmpeg", "-i", FINAL, "-vf", "freezedetect=n=0.0005:d=2", "-an", "-f", "null", "-"]).stderr
    freezes = re.findall(r"freeze_start: (\S+).*?freeze_end: (\S+)", fz, re.S)
    report.append(f"frozen segments (>=2 s): {freezes or 'none'}")
    lo = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", FINAL, "-map", "0:a",
             "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", lo)[-1]
    TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", lo)[-1]
    LRA = re.findall(r"LRA:\s+([\d.]+) LU", lo)[-1]
    report.append(f"audio loudness: I={I} LUFS  TP={TP} dBTP  LRA={LRA} LU")

    srt = open(os.path.join(VID, "output", "subtitles.en.srt"), encoding="utf-8").read()
    cues = [b.split("\n", 2)[2].strip() for b in srt.strip().split("\n\n")]
    ok = cues == [t for _, _, t in story.LINES]
    report.append(f"subtitles match narration exactly: {ok} ({len(cues)} cues)")
    txt = "\n".join(report)
    open(os.path.join(QA, "report.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
