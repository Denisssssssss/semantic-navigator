from fastapi import FastAPI, Query
from typing import List

import time_code_service

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/api/v1/timecode/{video_id}")
async def get_time_codes(video_id: str, key_words: List[str] = Query(None)):
    return time_code_service.get_semantic_time_codes(video_id, key_words)


