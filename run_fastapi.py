import uvicorn
from main import create_fastapi_app

if __name__ == "__main__":
    # Create the FastAPI app
    app = create_fastapi_app()
    
    # Run the server with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )