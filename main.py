import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html

from endpoints import auth, physicians, appointments, payments, insurance, chatbot
from db.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Clinic Appointment and Chatbot API",
    description="Backend API for clinic appointment booking and WhatsApp chatbot integration",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, limit this to your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"An unexpected error occurred: {str(exc)}"}
    )

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(physicians.router, prefix="/physicians", tags=["Physician Management"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(insurance.router, prefix="/insurance", tags=["Insurance"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["WhatsApp Chatbot"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Clinic Appointment and Chatbot API"}

# Custom Swagger UI with dark theme
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
