# import asyncio
# import fractions
# from typing import Any
# import av
# import numpy as np
# from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
# from fastapi import APIRouter, Body, HTTPException, Request, Response, WebSocket


# # カスタムの音声トラックを定義（440Hz音源）
# class ToneStreamTrack(MediaStreamTrack):
#     """440Hzのサイン波を生成するカスタムメディアトラック"""
    
#     kind = "audio"
    
#     def __init__(self):
#         super().__init__()
#         self._sample_rate = 48000
#         self._samples_per_frame = 960
#         self._timestamp = 0
#         self._freq = 440
#         self._amplitude = 0.5
#         self._phase = 0
        
#     async def recv(self):
#         await asyncio.sleep(self._samples_per_frame / self._sample_rate)
        
#         t = np.arange(self._samples_per_frame) + self._phase
#         samples = self._amplitude * np.sin(2 * np.pi * self._freq * t / self._sample_rate)
        
#         self._phase = (self._phase + self._samples_per_frame) % self._sample_rate
        
#         # 各サンプルを16ビット整数に変換
#         samples_int16 = (samples * 32767).astype(np.int16).reshape(-1, 1)
#         print(f"{samples_int16.shape=}")
        
#         # ステレオデータ（同じ波形を左右チャネルに複製）
#         stereo_samples = np.stack((samples_int16, samples_int16), axis=0)

#         print(f"stereo_samples: {stereo_samples.shape=}")
        
#         # AudioFrameをステレオサンプルから作成
#         frame = av.AudioFrame.from_ndarray(
#             samples_int16.T,
#             format="s16",
#             layout="stereo",
#         )
#         frame.sample_rate = self._sample_rate
#         frame.time_base = fractions.Fraction(1, self._sample_rate)
#         frame.pts = self._timestamp
#         self._timestamp += self._samples_per_frame
        
#         return frame

# def generate_router():
    
#     pcs = set()

#     router = APIRouter(prefix="/webrtc")

#     @router.post("/offer")
#     async def offer(request: Request):
#         params = await request.json()
#         offer = RTCSessionDescription(
#             sdp=params["sdp"],
#             type=params["type"]
#         )

#         pc = RTCPeerConnection()
#         pcs.add(pc)

#         @pc.on("connectionstatechange")
#         async def on_connectionstatechange():
#             if pc.connectionState == "failed" or pc.connectionState == "closed":
#                 if pc in pcs:
#                     pcs.discard(pc)

#         # 440Hz音声トラックを追加
#         tone_track = ToneStreamTrack()
#         pc.addTrack(tone_track)

#         await pc.setRemoteDescription(offer)
#         answer = await pc.createAnswer()
#         await pc.setLocalDescription(answer)

#         return {
#             "sdp": pc.localDescription.sdp,
#             "type": pc.localDescription.type
#         }
    
#     return router