#!/usr/bin/env python3
"""
PDF extraction utility for importing data from PDF documents.
This module provides functions to extract various types of data 
from PDF files and format it for database insertion.
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

import PyPDF2
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        raise

def extract_doctors_data(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract doctor information from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing doctor information
    """
    text = extract_text_from_pdf(pdf_path)
    
    # Example regex patterns for doctor information
    name_pattern = r"Dr\.\s+([\w\s]+)"
    specialty_pattern = r"Specialty:\s+([\w\s&]+)"
    qualification_pattern = r"Qualification:\s+([\w\s,&.]+)"
    experience_pattern = r"Experience:\s+(\d+)\s+years"
    
    # Find all matches
    doctor_names = re.findall(name_pattern, text)
    specialties = re.findall(specialty_pattern, text)
    qualifications = re.findall(qualification_pattern, text)
    experiences = re.findall(experience_pattern, text)
    
    # Combine the data
    doctors_data = []
    for i in range(min(len(doctor_names), len(specialties), len(qualifications), len(experiences))):
        doctor = {
            "name": doctor_names[i].strip(),
            "specialty": specialties[i].strip(),
            "qualification": qualifications[i].strip(),
            "experience_years": int(experiences[i]),
            "consultation_price": 500.0,  # Default price
            "languages": ["English"],  # Default language
            "profile_image": None,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        doctors_data.append(doctor)
    
    return doctors_data

def extract_treatments_data(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract treatment information from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing treatment information
    """
    text = extract_text_from_pdf(pdf_path)
    
    # Example regex patterns for treatment information
    treatment_pattern = r"Treatment:\s+([\w\s&()-]+)"
    specialty_pattern = r"Specialty:\s+([\w\s&]+)"
    description_pattern = r"Description:\s+([\w\s.,;:&()'-]+)(?=Treatment:|Specialty:|$)"
    price_pattern = r"Price Range:\s+(\d+)-(\d+)\s+AED"
    
    # Find all matches
    treatment_names = re.findall(treatment_pattern, text)
    specialties = re.findall(specialty_pattern, text)
    descriptions = re.findall(description_pattern, text)
    price_ranges = re.findall(price_pattern, text)
    
    # Combine the data
    treatments_data = []
    for i in range(min(len(treatment_names), len(specialties), len(descriptions))):
        price_range = {"min": 1000, "max": 5000}  # Default price range
        if i < len(price_ranges):
            price_range = {"min": float(price_ranges[i][0]), "max": float(price_ranges[i][1])}
        
        treatment = {
            "name": treatment_names[i].strip(),
            "specialty": specialties[i].strip(),
            "description": descriptions[i].strip(),
            "price_range": price_range,
            "duration_minutes": 60,  # Default duration
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        treatments_data.append(treatment)
    
    return treatments_data

def extract_packages_data(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract medical package information from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing medical package information
    """
    text = extract_text_from_pdf(pdf_path)
    
    # Example regex patterns for package information
    package_pattern = r"Package:\s+([\w\s&()-]+)"
    description_pattern = r"Description:\s+([\w\s.,;:&()'-]+)(?=Package:|Price:|Services:|$)"
    price_pattern = r"Price:\s+(\d+)\s+AED"
    services_pattern = r"Services:\s+([\w\s.,;:&()'-]+)(?=Package:|Price:|Description:|$)"
    
    # Find all matches
    package_names = re.findall(package_pattern, text)
    descriptions = re.findall(description_pattern, text)
    prices = re.findall(price_pattern, text)
    services_lists = re.findall(services_pattern, text)
    
    # Combine the data
    packages_data = []
    for i in range(min(len(package_names), len(descriptions))):
        price = 1500.0  # Default price
        if i < len(prices):
            price = float(prices[i])
        
        services = ["General Checkup"]  # Default services
        if i < len(services_lists):
            services = [s.strip() for s in services_lists[i].split(',')]
        
        package = {
            "name": package_names[i].strip(),
            "description": descriptions[i].strip(),
            "price": price,
            "duration_minutes": 120,  # Default duration
            "services": services,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        packages_data.append(package)
    
    return packages_data

def extract_clinic_info(pdf_path: str) -> Dict[str, Any]:
    """
    Extract clinic information from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing clinic information
    """
    text = extract_text_from_pdf(pdf_path)
    
    # Example regex patterns for clinic information
    name_pattern = r"Clinic Name:\s+([\w\s&]+)"
    address_pattern = r"Address:\s+([\w\s.,;:&()'-]+)"
    phone_pattern = r"Phone:\s+([\d+-]+)"
    email_pattern = r"Email:\s+([\w@.]+)"
    hours_pattern = r"Hours:\s+([\w\s.,;:&()'-]+)(?=Clinic Name:|Address:|Phone:|Email:|$)"
    
    # Find all matches
    name_match = re.search(name_pattern, text)
    address_match = re.search(address_pattern, text)
    phone_match = re.search(phone_pattern, text)
    email_match = re.search(email_pattern, text)
    hours_match = re.search(hours_pattern, text)
    
    # Extract the data
    name = "Valiant Clinic"  # Default name
    if name_match:
        name = name_match.group(1).strip()
    
    address = "Dubai Healthcare City"  # Default address
    if address_match:
        address = address_match.group(1).strip()
    
    phone = "+971-X-XXX-XXXX"  # Default phone
    if phone_match:
        phone = phone_match.group(1).strip()
    
    email = "info@valiantclinic.com"  # Default email
    if email_match:
        email = email_match.group(1).strip()
    
    # Default working hours
    working_hours = {
        "Monday": "8:00-21:00",
        "Tuesday": "8:00-21:00",
        "Wednesday": "8:00-21:00",
        "Thursday": "8:00-21:00",
        "Friday": "8:00-21:00",
        "Saturday": "8:00-21:00",
        "Sunday": "8:00-21:00"
    }
    
    if hours_match:
        hours_text = hours_match.group(1).strip()
        # Parse hours_text to update working_hours if needed
    
    clinic_info = {
        "name": name,
        "description": "A premium healthcare facility providing world-class medical services.",
        "address": address,
        "phone": phone,
        "email": email,
        "website": "https://valiantclinic.com",
        "working_hours": working_hours,
        "created_at": datetime.utcnow(),
    }
    
    return clinic_info

def save_extracted_data_as_json(data: Any, output_path: str) -> None:
    """
    Save extracted data as JSON file for review before database insertion.
    
    Args:
        data: Data to save
        output_path: Path to save the JSON file
    """
    class ObjectIdEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super(ObjectIdEncoder, self).default(obj)
    
    try:
        with open(output_path, 'w') as file:
            json.dump(data, file, cls=ObjectIdEncoder, indent=2)
        logger.info(f"Data saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving data to {output_path}: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    doctors_pdf = "attached_assets/Doctors.pdf"
    treatments_pdf = "attached_assets/Treatments.pdf"
    packages_pdf = "attached_assets/Packages.pdf"
    about_pdf = "attached_assets/About Us (1).pdf"
    
    if os.path.exists(doctors_pdf):
        doctors_data = extract_doctors_data(doctors_pdf)
        save_extracted_data_as_json(doctors_data, "extracted_doctors.json")
    
    if os.path.exists(treatments_pdf):
        treatments_data = extract_treatments_data(treatments_pdf)
        save_extracted_data_as_json(treatments_data, "extracted_treatments.json")
    
    if os.path.exists(packages_pdf):
        packages_data = extract_packages_data(packages_pdf)
        save_extracted_data_as_json(packages_data, "extracted_packages.json")
    
    if os.path.exists(about_pdf):
        clinic_info = extract_clinic_info(about_pdf)
        save_extracted_data_as_json(clinic_info, "extracted_clinic_info.json")