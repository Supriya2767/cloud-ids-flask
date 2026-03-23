import requests
import threading

url = "https://tribal-willard-paleobiological.ngrok-free.dev/products"

def attack():
    for _ in range(20):
        try:
            requests.get(url)
        except:
            pass

threads = []

for i in range(50):
    t = threading.Thread(target=attack)
    t.start()
    threads.append(t)

for t in threads:
    t.join()