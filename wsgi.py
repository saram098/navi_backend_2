from main import fastapi_app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=5001)