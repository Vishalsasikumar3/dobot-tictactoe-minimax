from serial.tools import list_ports
try:
    from pydobot import Dobot
except ImportError:
    from pydobot2 import Dobot

def pose(bot):
    p = bot.pose() if hasattr(bot, "pose") else bot.get_pose()
    if not p or len(p) < 4: raise RuntimeError("Pose not available")
    return p

def joints(bot, full):
    for name in ("angles","get_angles","joint_angles","get_joint_angles"):
        if hasattr(bot, name):
            try:
                a = getattr(bot, name)()
                if a and len(a) >= 4: return a[:4]
            except Exception: pass
    return full[4:8] if len(full) >= 8 else None

def main():
    ports = [p.device for p in list_ports.comports()]
    print("Ports found:", ports)
    for dev in ports:
        bot=None
        try:
            bot = Dobot(port=dev)
            try: bot.speed(60,60)
            except Exception: pass
            p = pose(bot); x,y,z,r = p[:4]
            print(f"CONNECTED: {dev}")
            print(f"Pose:   x={x:.2f}  y={y:.2f}  z={z:.2f}  r={r:.2f}")
            j = joints(bot, p)
            if j:
                j1,j2,j3,j4 = j
                print(f"Joints: j1={j1:.2f}  j2={j2:.2f}  j3={j3:.2f}  j4={j4:.2f}")
            else:
                print("Joints: unavailable")
            return
        except Exception:
            pass
        finally:
            try:
                if bot: bot.close()
            except Exception: pass
    print("No Dobot found — close DobotStudio, check cable/USB, try a different port.")

if __name__ == "__main__":
    main()
