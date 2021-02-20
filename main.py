from aiohttp import ClientSession
from asyncio import get_event_loop, gather
from os import environ as env
from itertools import cycle
from time import time, sleep

# Give MAX time to boot
sleep(5)

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class ToxClient:
    def __init__(self):
        self.sess = ClientSession()
        self.detectors = cycle([f"http://{url}/model/predict" for url in env["DETECTORS"].split(";")])

    async def getres(self, data: dict):
        url = next(self.detectors)

        text = data["c"]
        try:
            response = await self.sess.post(url, json={"text":[text]})
            json = await response.json()
            json = {
                "c":text,
                "a":data["a"],
                "values": json["results"][0]["predictions"]
            }
        except:
            json = None

        return json

    async def getall(self, texts: list):
        return await gather(*[self.getres(t) for t in texts])

    async def post_results(self, wuid: int, results: list):
        data = {
            "data":{
                "items":results
            }
        }

        await self.sess.post(env["URL"] + f"/submit/{wuid}", headers={"Authorization": env["API_TOKEN"]}, json=data)

    async def get_wu(self):
        resp = await self.sess.get(env["URL"] + "/task", headers={"Authorization": env["API_TOKEN"]})
        return await resp.json()

    async def run_wus(self):
        while True:
            st = time()
            wu = await self.get_wu()
            wuid = wu["id"]
            data = wu["data"]

            print(f"[{wuid}] Running...")

            allwus = []

            for i, chunk in enumerate(chunks(data, 10)):
                print(f"[{wuid}] Detecting chunk: ", i)
                res = await self.getall(chunk)
                allwus.extend(res)

            allwus = [r for r in allwus if r]
            await self.post_results(wuid, allwus)
            print(f"[{wuid}] Finished. ({round(time() - st)}s)")

    def run(self):
        loop = get_event_loop()
        loop.run_until_complete(self.run_wus())

t = ToxClient()
t.run()