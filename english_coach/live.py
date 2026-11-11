import asyncio, base64, io, json
from pathlib import Path
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from core import SYSTEM
app=FastAPI()
model=None
lock=asyncio.Lock()
def transcribe(raw):
 global model
 from faster_whisper import WhisperModel
 if model is None: model=WhisperModel('base.en',device='cpu',compute_type='int8')
 segments,_=model.transcribe(io.BytesIO(raw),language='en',vad_filter=True)
 return ' '.join(s.text for s in segments).strip()
@app.get('/')
def home(): return FileResponse(Path(__file__).with_name('live.html'))
@app.websocket('/voice')
async def voice(ws:WebSocket):
 if ws.headers.get('origin') not in {'http://127.0.0.1:8502','http://localhost:8502'}:
  await ws.close(code=1008); return
 await ws.accept()
 tasks=set(); history=[]
 async def turn(m):
  async def send(kind,**kw): await ws.send_json(dict(type=kind,id=m['id'],**kw))
  try:
   raw=base64.b64decode(m['audio'],validate=True)
   if len(raw)>4000000: raise ValueError('Áudio longo demais')
   await send('status',text='Transcrevendo…')
   async with lock:
    worker=asyncio.create_task(asyncio.to_thread(transcribe,raw))
    try: text=await asyncio.shield(worker)
    except asyncio.CancelledError:
     await worker
     raise
   if not text:
    await send('status',text='Não detectei fala. Pode repetir?'); return
   history.append(dict(role='user',content=text))
   await send('transcript',text=text)
   selected=m.get('model','qwen2.5:7b')
   if selected not in {'qwen2.5:7b','qwen2.5:3b'}: raise ValueError('Modelo inválido')
   answer=''
   async with httpx.AsyncClient(timeout=180) as client:
    async with client.stream('POST','http://127.0.0.1:11434/api/chat',json={'model':selected,'messages':[dict(role='system',content=SYSTEM+'\nVoice mode: respond in English, at most three short sentences.')]+history[-16:],'stream':True,'options':{'num_ctx':4096}}) as response:
     response.raise_for_status()
     async for line in response.aiter_lines():
      if not line: continue
      item=json.loads(line)
      if item.get('error'): raise ValueError(item['error'])
      chunk=item.get('message',{}).get('content',''); answer+=chunk
      await send('chunk',text=chunk)
   history.append(dict(role='assistant',content=answer)); history[:]=history[-16:]
   await send('done')
  except asyncio.CancelledError: raise
  except Exception as exc: await send('error',text=f'Falha: {exc}. Confira o Ollama e o modelo instalado.')
 try:
  while True:
   m=await ws.receive_json()
   if m.get('type') in {'interrupt','audio'}:
    for t in list(tasks):
     if not t.cancelling(): t.cancel()
    if m['type']=='audio':
     t=asyncio.create_task(turn(m)); tasks.add(t); t.add_done_callback(tasks.discard)
 except WebSocketDisconnect: pass
 finally:
  for t in tasks:
   if not t.cancelling(): t.cancel()
