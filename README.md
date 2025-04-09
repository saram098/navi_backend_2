# Clinic Appointment and Chatbot API

A backend system for a clinic appointment platform with WhatsApp chatbot integration, built with FastAPI and MongoDB.

## Overview

This backend system provides a comprehensive solution for clinic appointment management and patient interaction through WhatsApp chatbot integration. It includes features for appointment scheduling, physician management, user authentication, payments processing, insurance verification, and an AI-powered chatbot for patient interactions.

## Features

- **Authentication**: User registration, email verification, JWT-based authentication
- **Physician Management**: Store and query information about physicians
- **Appointments**: Book, view, update, and cancel appointments
- **Payments**: Stripe integration for payment processing
- **Insurance Verification**: Check insurance coverage using Emirates ID
- **WhatsApp Chatbot**: Interact via WhatsApp using Twilio and OpenAI

## Technology Stack

- **Backend Framework**: FastAPI
- **Database**: MongoDB (using Motor for async operations)
- **External Services**:
  - Twilio for WhatsApp integration
  - OpenAI for chatbot intelligence
  - Stripe for payment processing
- **Authentication**: JWT (JSON Web Tokens)

## Project Structure

```
.
├── agents/               # Chatbot agent code
├── db/                   # Database connection and operations
├── endpoints/            # API route definitions
├── models/               # Pydantic models for data validation
├── services/             # External service integrations
├── settings/             # Configuration settings
├── static/               # Static files for documentation
├── utils/                # Utility functions
├── main.py               # Main application entry point
├── run_fastapi.py        # Script to run FastAPI application
└── README.md             # Project documentation
```

## Running the Application

The application can be run in two modes:

### 1. Simple WSGI mode (default with gunicorn)

This mode serves a simple API with static file support, suitable for deployment:

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### 2. Full FastAPI mode (using uvicorn)

This mode enables all FastAPI features including auto-documentation:

```bash
python run_fastapi.py
# OR
python -m uvicorn main:create_fastapi_app --host 0.0.0.0 --port 5000
```

## API Documentation

When running in FastAPI mode, interactive documentation is available at:

- `/docs` - SwaggerUI (interactive API documentation)
- `/redoc` - ReDoc (alternative API documentation)

A static overview of the API is also available at `/static/api-docs.html`.

## Environment Variables

The application requires the following environment variables:

- `MONGO_URI` - MongoDB connection string
- `SECRET_KEY` - Secret key for JWT encoding
- `STRIPE_SECRET_KEY` - Stripe API key for payments
- `TWILIO_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `TWILIO_PHONE_NUMBER` - Twilio phone number for WhatsApp
- `OPENAI_API_KEY` - OpenAI API key for chatbot intelligence