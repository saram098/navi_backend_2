#!/usr/bin/env python3
"""
Script to import data from PDF files into MongoDB.
This script extracts data from PDF files and inserts it into the appropriate collections.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import motor.motor_asyncio
from bson import ObjectId
from utils.pdf_extractor import (
    extract_doctors_data,
    extract_treatments_data,
    extract_packages_data,
    extract_clinic_info
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get MongoDB connection string from environment variable
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = "clinic_db"

async def connect_to_mongo():
    """Connect to MongoDB Atlas."""
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Verify the connection is successful
        await client.admin.command('ping')
        logger.info("Connected to MongoDB Atlas successfully")
        
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def import_doctors_data(db, pdf_path: str) -> int:
    """
    Import doctor data from PDF into MongoDB.
    
    Args:
        db: MongoDB database connection
        pdf_path: Path to the PDF file
        
    Returns:
        Number of doctors imported
    """
    # Check if the file exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return 0
    
    # Extract data from PDF
    doctors_data = extract_doctors_data(pdf_path)
    if not doctors_data:
        logger.warning(f"No doctor data extracted from {pdf_path}")
        return 0
    
    # Generate example schedule for each doctor
    for doctor in doctors_data:
        # Add empty schedule for now
        doctor["schedule"] = []
    
    # Get existing physician names to avoid duplicates
    existing_names = set()
    existing_cursor = db.physicians.find({}, {"name": 1})
    async for doc in existing_cursor:
        existing_names.add(doc["name"])
    
    # Filter out existing physicians
    new_doctors = [doc for doc in doctors_data if doc["name"] not in existing_names]
    
    # Insert new physicians
    if new_doctors:
        result = await db.physicians.insert_many(new_doctors)
        logger.info(f"Imported {len(result.inserted_ids)} new doctors")
        return len(result.inserted_ids)
    else:
        logger.info("No new doctors to import")
        return 0

async def import_treatments_data(db, pdf_path: str) -> int:
    """
    Import treatment data from PDF into MongoDB.
    
    Args:
        db: MongoDB database connection
        pdf_path: Path to the PDF file
        
    Returns:
        Number of treatments imported
    """
    # Check if the file exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return 0
    
    # Extract data from PDF
    treatments_data = extract_treatments_data(pdf_path)
    if not treatments_data:
        logger.warning(f"No treatment data extracted from {pdf_path}")
        return 0
    
    # Get existing treatment names to avoid duplicates
    existing_names = set()
    existing_cursor = db.treatments.find({}, {"name": 1})
    async for doc in existing_cursor:
        existing_names.add(doc["name"])
    
    # Filter out existing treatments
    new_treatments = [doc for doc in treatments_data if doc["name"] not in existing_names]
    
    # Insert new treatments
    if new_treatments:
        result = await db.treatments.insert_many(new_treatments)
        logger.info(f"Imported {len(result.inserted_ids)} new treatments")
        return len(result.inserted_ids)
    else:
        logger.info("No new treatments to import")
        return 0

async def import_packages_data(db, pdf_path: str) -> int:
    """
    Import medical package data from PDF into MongoDB.
    
    Args:
        db: MongoDB database connection
        pdf_path: Path to the PDF file
        
    Returns:
        Number of packages imported
    """
    # Check if the file exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return 0
    
    # Extract data from PDF
    packages_data = extract_packages_data(pdf_path)
    if not packages_data:
        logger.warning(f"No medical package data extracted from {pdf_path}")
        return 0
    
    # Get existing package names to avoid duplicates
    existing_names = set()
    existing_cursor = db.medical_packages.find({}, {"name": 1})
    async for doc in existing_cursor:
        existing_names.add(doc["name"])
    
    # Filter out existing packages
    new_packages = [doc for doc in packages_data if doc["name"] not in existing_names]
    
    # Insert new packages
    if new_packages:
        result = await db.medical_packages.insert_many(new_packages)
        logger.info(f"Imported {len(result.inserted_ids)} new medical packages")
        return len(result.inserted_ids)
    else:
        logger.info("No new medical packages to import")
        return 0

async def import_clinic_info(db, pdf_path: str) -> bool:
    """
    Import clinic information from PDF into MongoDB.
    
    Args:
        db: MongoDB database connection
        pdf_path: Path to the PDF file
        
    Returns:
        True if successful, False otherwise
    """
    # Check if the file exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    # Extract data from PDF
    clinic_data = extract_clinic_info(pdf_path)
    if not clinic_data:
        logger.warning(f"No clinic information extracted from {pdf_path}")
        return False
    
    # Check if clinic info already exists
    existing_clinic = await db.clinic_info.find_one({"name": clinic_data["name"]})
    if existing_clinic:
        # Update existing clinic info
        await db.clinic_info.update_one(
            {"_id": existing_clinic["_id"]},
            {"$set": {**clinic_data, "updated_at": datetime.utcnow()}}
        )
        logger.info("Updated existing clinic information")
    else:
        # Insert new clinic info
        await db.clinic_info.insert_one(clinic_data)
        logger.info("Imported new clinic information")
    
    return True

async def main():
    """Main function to run the import process."""
    try:
        # Connect to MongoDB
        db = await connect_to_mongo()
        
        # Set paths to PDF files
        doctors_pdf = "attached_assets/Doctors.pdf"
        treatments_pdf = "attached_assets/Treatments.pdf"
        packages_pdf = "attached_assets/Packages.pdf"
        about_pdf = "attached_assets/About Us (1).pdf"
        
        # Import data from each PDF
        total_imported = 0
        
        # Import doctors
        if os.path.exists(doctors_pdf):
            doctors_count = await import_doctors_data(db, doctors_pdf)
            total_imported += doctors_count
        else:
            logger.warning(f"Doctors PDF not found: {doctors_pdf}")
        
        # Import treatments
        if os.path.exists(treatments_pdf):
            treatments_count = await import_treatments_data(db, treatments_pdf)
            total_imported += treatments_count
        else:
            logger.warning(f"Treatments PDF not found: {treatments_pdf}")
        
        # Import packages
        if os.path.exists(packages_pdf):
            packages_count = await import_packages_data(db, packages_pdf)
            total_imported += packages_count
        else:
            logger.warning(f"Packages PDF not found: {packages_pdf}")
        
        # Import clinic info
        if os.path.exists(about_pdf):
            success = await import_clinic_info(db, about_pdf)
            if success:
                total_imported += 1
        else:
            logger.warning(f"About PDF not found: {about_pdf}")
        
        logger.info(f"Import completed. Total items imported: {total_imported}")
    
    except Exception as e:
        logger.error(f"Error during import: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())