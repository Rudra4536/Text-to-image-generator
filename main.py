import os
import time
import io
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

API_KEY = os.getenv("POLLINATIONS_API_KEY")
if not API_KEY:
    raise RuntimeError("POLLINATIONS_API_KEY is missing from your .env file.")

app = FastAPI(title="AI Image Generator SaaS - Pollinations Edition")

# Mount the static directory to serve our frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

class PromptRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/generate")
async def generate_image(request: PromptRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    try:
        # 1. Clean and url-encode the text string so spaces/symbols don't break the web link
        encoded_prompt = urllib.parse.quote(request.prompt)
        
        # 2. Build the exact authenticated query string path using your API Key
        authenticated_url = f"https://image.pollinations.ai/p/{encoded_prompt}?model=flux&width=1024&height=1024&nologo=true&key={API_KEY}"
        
        # 3. Return the clean link directly to the frontend interface
        return {"image_url": authenticated_url}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected internal error: {str(e)}")

@app.get("/proxy-download")
async def proxy_download(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
        
    try:
        async with httpx.AsyncClient() as client:
            # Fetch the raw binary image data directly from Pollinations AI
            response = await client.get(url, timeout=20.0)
            response.raise_for_status()
            
            # Generate an integer timestamp for clean naming
            timestamp = int(time.time())
            
            # Pass the raw image byte buffer down to the client system
            return StreamingResponse(
                io.BytesIO(response.content), 
                media_type="image/png",
                headers={
                    "Content-Disposition": f"attachment; filename=imagineai-{timestamp}.png"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch image for download: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main.py:app", host="127.0.0.1", port=8000, reload=True)