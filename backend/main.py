import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Wella.AI Clinical System")

# ==========================
# 🔥 FIX: Absolute static path
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ==========================
# Middleware
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)

# ==========================
# Root → Landing page (NOT index.html)
# ==========================
@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "landing.html"))

# ==========================
# Clean route for triage
# ==========================
@app.get("/triage")
async def triage_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# ==========================
# Run
# ==========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)