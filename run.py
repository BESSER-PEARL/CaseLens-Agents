# run.py
import subprocess
import signal
import sys
import threading
import time

from agents.data_labeling_agent.data_labeling_agent import data_labeling_agent

# Launch Streamlit app
proc = subprocess.Popen(["streamlit", "run", "app/main.py"])

def shutdown(signum, frame):
    data_labeling_agent.stop()
    time.sleep(1)
    proc.kill()
    sys.exit(0)


idle = threading.Event()
while True:
    try:
        idle.wait(1)
    except BaseException as e:
        print('Closing app')
        shutdown(signal.SIGINT, None)
