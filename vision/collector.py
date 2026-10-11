#!/usr/bin/env python3
"""SWARMFLOW collector: MCU sensors (RouterBridge) -> WebSocket :8090. Run on egg.
WS in:  {"led":[r,g,b]}  -> MCU set_led
WS out: {"ts":..., "sensors":{...}, "mcu_ok":true, "camera":null}
"""
import asyncio, json, time
from aiohttp import web
from arduino.router_bridge import Bridge

POLL = 0.2
SOCK = "unix:///run/arduino-router.sock"
clients = set()

def read_dets():
    try:
        with open("/tmp/swarm_dets.json") as f:
            return json.load(f)
    except Exception:
        return None

def bridge_connect():
    b = Bridge(SOCK)
    b.connect()
    return b

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    clients.add(ws)
    try:
        async for msg in ws:
            if msg.type == 1:
                try:
                    cmd = json.loads(msg.data)
                    if "led" in cmd:
                        request.app["led_cmd"] = cmd["led"]
                    if "mode" in cmd:
                        request.app["led_mode"] = int(cmd["mode"])
                except Exception:
                    pass
    finally:
        clients.discard(ws)
    return ws

async def pump(app):
    b = None
    last_ok = 0.0
    led_cmd = None
    mode_cmd = None
    while True:
        try:
            if b is None:
                b = bridge_connect()
            s = b.call("read_sensors", timeout=2.0)
            if isinstance(s, (str, bytes)):
                s = json.loads(s)
            last_ok = time.time()
            led = app.get("led_cmd")
            if led != led_cmd:
                b.call("set_led", int(led[0]), int(led[1]), int(led[2]), timeout=2.0)
                led_cmd = led
            md = app.get("led_mode")
            if md is not None and md != mode_cmd:
                b.call("set_mode", md, timeout=2.0)
                mode_cmd = md
            payload = json.dumps({
                "ts": time.time(), "mcu_ok": True, "mcu_age_s": 0,
                "sensors": s, "camera": read_dets(),
            })
        except Exception as e:
            app["err"] = str(e)[:120]
            payload = json.dumps({
                "ts": time.time(), "mcu_ok": False,
                "mcu_age_s": round(time.time() - last_ok, 1),
                "err": app.get("err"), "sensors": None, "camera": read_dets(),
            })
            b = None
            await asyncio.sleep(0.5)
        for ws in list(clients):
            try:
                await ws.send_str(payload)
            except Exception:
                clients.discard(ws)
        await asyncio.sleep(POLL)

async def main():
    app = web.Application()
    app.router.add_get("/ws", ws_handler)
    app["led_cmd"] = [0, 0, 0]
    app["bg"] = asyncio.create_task(pump(app))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 8090).start()
    await asyncio.Event().wait()

asyncio.run(main())
