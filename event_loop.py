# event_loop.py
import asyncio
import threading

background_loop = asyncio.new_event_loop()

def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_background_loop, args=(background_loop,), daemon=True).start()
