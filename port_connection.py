#!/usr/bin/env python3
import time, inspect
from serial.tools import list_ports

# Import pydobot (fallback to pydobot2)
try:
    from pydobot import Dobot
except ImportError:
    from pydobot2 import Dobot  # type: ignore

def ctor(dev: str):
    """Handle Dobot() vs Dobot(port=...) constructor styles."""
    params = inspect.signature(Dobot).parameters
    try:
        if "port" in params:
            return Dobot(port=dev)
        else:
            return Dobot(dev)  # type: ignore[call-arg]
    except TypeError:
        # Try the other style as a fallback
        try:
            return Dobot(dev)  # type: ignore[call-arg]
        except Exception:
            return Dobot(port=dev)

def pose(bot):
    getter = getattr(bot, "pose", None) or getattr(bot, "get_pose", None)
    if not getter:
        raise RuntimeError("No pose method on Dobot object")
    p = getter()
    if not p or len(p) < 4:
        raise RuntimeError("Pose not available")
    return p

def joints(bot, full):
    for name in ("angles", "get_angles", "joint_angles", "get_joint_angles"):
        if hasattr(bot, name):
            try:
                a = getattr(bot, name)()
                if a and len(a) >= 4:
                    return a[:4]
            except Exception:
                pass
    return full[4:8] if len(full) >= 8 else None

def main():
    ports = [p.device for p in list_ports.comports()]
    print("Ports found:", ports)
    for dev in ports:
        bot = None
        try:
            bot = ctor(dev)

            # Optional speed setup; ignore if unsupported
            for setter in ("speed", "set_speed"):
                if hasattr(bot, setter):
                    try:
                        getattr(bot, setter)(60, 60)
                    except Exception:
                        pass

            time.sleep(1.0)  # let firmware settle

            p = pose(bot)
            x, y, z, r = p[:4]
            print(f"CONNECTED: {dev}")
            print(f"Pose:   x={x:.2f}  y={y:.2f}  z={z:.2f}  r={r:.2f}")

            j = joints(bot, p)
            if j:
                j1, j2, j3, j4 = j
                print(f"Joints: j1={j1:.2f}  j2={j2:.2f}  j3={j3:.2f}  j4={j4:.2f}")
            else:
                print("Joints: unavailable")
            return  # success
        except Exception as e:
            print(f"FAILED on {dev}: {e}")
        finally:
            try:
                if bot:
                    bot.close()
            except Exception:cd "/Users/vishals/yolo/midterm ras ai"
./.venv/bin/python quick_probe.py

                pass

    print("No Dobot found — close DobotStudio, check cable/USB, try a different USB port.")

if __name__ == "__main__":
    main()
