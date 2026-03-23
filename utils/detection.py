from datetime import datetime, timedelta
from config import REQUEST_THRESHOLD, BLOCK_DURATION_MINUTES

blacklist = {}

def check_blacklist(ip):
    if ip in blacklist:
        if datetime.now() < blacklist[ip]:
            return True
        else:
            del blacklist[ip]
    return False


def detect_attack(ip, request_rate):
    if request_rate > REQUEST_THRESHOLD:
        blacklist[ip] = datetime.now() + timedelta(minutes=BLOCK_DURATION_MINUTES)
        return "DDoS"
    return "Normal"