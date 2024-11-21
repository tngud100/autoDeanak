from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, websockets
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from src.controller import autoService_controller
from src.controller import req_deanak_controller
from src.controller import deanak_controller
from src.controller import ten_min_controller
import warnings



warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# FastAPI 애플리케이션 설정
app = FastAPI()

origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(autoService_controller.router)
app.include_router(req_deanak_controller.router)
app.include_router(deanak_controller.router)
app.include_router(ten_min_controller.router)


app.mount("/static", StaticFiles(directory="./static"), name="static")

@app.on_event("startup")
async def startup_event():
    print("App started")

@app.on_event("shutdown")
async def shutdown_event():
    print("App shutdown")

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)

    