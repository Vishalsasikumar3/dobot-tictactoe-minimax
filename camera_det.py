# opencv_to_gemini.py
# Capture a camera frame with OpenCV, send to Gemini, print inference.

import os
import sys
import cv2
from typing import Optional

# Gemini SDK
from google import genai
from google.genai import types

MODEL_NAME = "gemini-2.5-flash"  # fast & multimodal

PROMPT = "Describe this scene in one sentence. Also list any objects you can identify."

def find_camera_index(max_index: int = 8) -> int:
    """Return the first camera index that opens and delivers a frame."""
    for i in range(max_index + 1):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ok, _ = cap.read()
            cap.release()
            if ok:
                return i
    raise RuntimeError("No working camera found. Plug one in or try a different index.")

def capture_frame(index: int) -> "tuple[bytes, any]":
    """Open camera at `index`, preview, SPACE to capture, ESC to quit. Returns (jpeg_bytes, frame_bgr)."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open camera index {index}")

    cv2.namedWindow("Camera (SPACE = capture, ESC = quit)", cv2.WINDOW_NORMAL)
    jpeg_bytes: Optional[bytes] = None
    frame_bgr = None

    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        cv2.imshow("Camera (SPACE = capture, ESC = quit)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        if key == 32:  # SPACE
            # Encode to JPEG to keep request small
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not ok:
                print("Failed to encode frame.")
                continue
            jpeg_bytes = buf.tobytes()
            frame_bgr = frame.copy()
            break

    cap.release()
    cv2.destroyAllWindows()

    if jpeg_bytes is None:
        raise RuntimeError("No image captured.")
    return jpeg_bytes, frame_bgr

def infer_with_gemini(image_bytes: bytes, prompt: str) -> str:
    """Send the image + prompt to Gemini and return the text response."""
    # The client reads GEMINI_API_KEY from the environment by default.
    client = genai.Client()

    result = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt,
        ],
    )
    return (result.text or "").strip()

def main():
    # Basic env guard
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY is not set in your environment.", file=sys.stderr)
        sys.exit(1)

    print("Scanning for cameras...")
    cam_idx = find_camera_index()
    print(f"Using camera index: {cam_idx}")

    print("Opening camera preview… Press SPACE to capture, ESC to quit.")
    jpg, _ = capture_frame(cam_idx)

    print("Sending image to Gemini…")
    try:
        text = infer_with_gemini(jpg, PROMPT)
        print("\n=== Gemini response ===")
        print(text if text else "[No text in response]")
    except Exception as e:
        print(f"Gemini API error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
