from fastapi import FastAPI, Query
from typing import List

from starlette.middleware.cors import CORSMiddleware

import time_code_service

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)



@app.get("/api/v1/timecode/{video_id}")
async def get_time_codes(video_id: str, key_words: str):
    return time_code_service.get_semantic_time_codes(video_id, key_words.split(','))
