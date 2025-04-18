import uvicorn
from main import create_fastapi_app

if __name__ == "__main__":
    app = create_fastapi_app()
    uvicorn.run(app, host="0.0.0.0", port=5000)