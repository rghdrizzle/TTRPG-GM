from app.db import db
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from app.services import gm
from sse_starlette.sse import EventSourceResponse 
# async def chat(query: str,isEnd: bool):


async def event_generator(): 
        response = await ser.ChatCompletion.acreate( 
            model="gpt-4", 
            messages=[{"role": "user", "content": prompt}], 
            stream=True, 
   ) 
   async for chunk in response: 
      if request.client_disconnected: 
         break 
      if "choices" in chunk: 
          content = chunk["choices"][0].get("delta", {}).get("content", "") 
          if content: 
              yield f"data: {content}\n\n" 

    yield "data: [DONE]\n\n" 
     