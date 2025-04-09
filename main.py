import os
import sys
from inspect import isclass
from typing import Callable
import json
import mimetypes

# Import local modules explicitly to avoid conflicts with installed packages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a simple WSGI app that will handle our request and return a meaningful message
def simple_app(environ, start_response):
    """A simple WSGI application that works with gunicorn."""
    path_info = environ.get('PATH_INFO', '/')
    
    # Serve static files if available
    if path_info == '/':
        # Serve the index.html file
        try:
            with open('static/index.html', 'rb') as f:
                content = f.read()
            status = '200 OK'
            headers = [('Content-type', 'text/html')]
            start_response(status, headers)
            return [content]
        except FileNotFoundError:
            # Fall back to JSON response if static file not found
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [b'{"message": "Welcome to the Clinic Appointment and Chatbot Platform API. Use /docs for documentation"}']
    
    # Serve static files from the static directory
    elif path_info.startswith('/static/'):
        file_path = path_info[1:]  # Remove the leading slash
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
                
            status = '200 OK'
            headers = [('Content-type', content_type)]
            start_response(status, headers)
            return [content]
        except FileNotFoundError:
            # Try alternate path handling (no leading static)
            try:
                if path_info.startswith('/static/'):
                    alt_path = 'static/' + path_info[8:]  # Remove the '/static/' prefix and add 'static/' directory
                    with open(alt_path, 'rb') as f:
                        content = f.read()
                    
                    # Determine content type
                    content_type, _ = mimetypes.guess_type(alt_path)
                    if not content_type:
                        content_type = 'application/octet-stream'
                        
                    status = '200 OK'
                    headers = [('Content-type', content_type)]
                    start_response(status, headers)
                    return [content]
            except FileNotFoundError:
                pass
                
            status = '404 Not Found'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [b'{"error": "File not found"}']
    
    # Default response for API routes
    status = '200 OK'
    headers = [('Content-type', 'application/json')]
    start_response(status, headers)
    
    # Return a simple API message
    message = {
        "message": "Welcome to the Clinic Appointment and Chatbot Platform API",
        "version": "1.0",
        "documentation": "Run the FastAPI app for interactive docs at /docs"
    }
    return [json.dumps(message).encode('utf-8')]

# Use this app as our main app - it's compatible with gunicorn
app = simple_app

# Instructions for using FastAPI with Uvicorn
# If you want to run FastAPI instead with Uvicorn, run:
# ```
# python run_fastapi.py
# ```

# This function will be called by uvicorn when needed
def create_fastapi_app():
    """Create and return a FastAPI application."""
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
    from fastapi.openapi.docs import get_swagger_ui_html
    from fastapi.staticfiles import StaticFiles
    
    from endpoints.auth import router as auth_router
    from endpoints.physicians import router as physicians_router
    from endpoints.appointments import router as appointments_router
    from endpoints.payments import router as payments_router
    from endpoints.insurance import router as insurance_router
    from endpoints.chatbot import router as chatbot_router
    from db.database import connect_to_mongo, close_mongo_connection

    fastapi_app = FastAPI(
        title="Clinic Appointment and Chatbot API",
        description="Backend API for clinic appointment booking and WhatsApp chatbot integration",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # Configure CORS
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, limit this to your actual domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Database connection events
    fastapi_app.add_event_handler("startup", connect_to_mongo)
    fastapi_app.add_event_handler("shutdown", close_mongo_connection)

    # Exception handler
    @fastapi_app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"message": f"An unexpected error occurred: {str(exc)}"}
        )

    # Include routers
    fastapi_app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    fastapi_app.include_router(physicians_router, prefix="/physicians", tags=["Physician Management"])
    fastapi_app.include_router(appointments_router, prefix="/appointments", tags=["Appointments"])
    fastapi_app.include_router(payments_router, prefix="/payments", tags=["Payments"])
    fastapi_app.include_router(insurance_router, prefix="/insurance", tags=["Insurance"])
    fastapi_app.include_router(chatbot_router, prefix="/chatbot", tags=["WhatsApp Chatbot"])
    
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    # Mount static files directory
    fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

    @fastapi_app.get("/", tags=["Root"])
    async def root():
        return FileResponse("static/index.html")

    # Custom Swagger UI with dark theme
    @fastapi_app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=fastapi_app.openapi_url,
            title=fastapi_app.title + " - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
        )
        
    return fastapi_app
