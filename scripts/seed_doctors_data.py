#!/usr/bin/env python3
"""
Script to seed the database with initial doctor data and clinic information.
Run this script to populate the database with doctors from the provided PDFs.
"""

import asyncio
import motor.motor_asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from bson import ObjectId

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

async def seed_clinic_data(db):
    """Seed clinic information data."""
    # Check if clinic data already exists
    existing_clinic = await db.clinic_info.find_one({"name": "Valiant Clinic"})
    if existing_clinic:
        logger.info("Clinic information already exists, skipping")
        return
    
    clinic_data = {
        "name": "Valiant Clinic",
        "description": "At Valiant Clinic, we believe healthcare should be as comforting as it is effective. Our serene, modern facilities provide a luxurious environment where your health is our top priority.",
        "address": "City Walk, Dubai, United Arab Emirates",
        "phone": "+971-X-XXX-XXXX",  # Replace with actual number
        "email": "info@valiantclinic.com",
        "website": "https://valiantclinic.com",
        "working_hours": {
            "Monday": "8:00-21:00",
            "Tuesday": "8:00-21:00",
            "Wednesday": "8:00-21:00",
            "Thursday": "8:00-21:00",
            "Friday": "8:00-21:00",
            "Saturday": "8:00-21:00",
            "Sunday": "8:00-21:00"
        },
        "mission": "To provide world-class healthcare by integrating advanced medical technology with a patient-first approach, empowering patients with knowledge and top-tier medical care for their well-being.",
        "vision": "To be the leading healthcare clinic in Dubai, setting the benchmark for medical excellence, innovation, and patient satisfaction.",
        "created_at": datetime.utcnow(),
    }
    
    await db.clinic_info.insert_one(clinic_data)
    logger.info("Clinic information seeded successfully")

async def seed_doctors_data(db):
    """Seed doctors data from the provided PDF content."""
    # Check if doctors already exist
    existing_count = await db.physicians.count_documents({})
    if existing_count > 0:
        logger.info(f"{existing_count} physicians already exist, skipping")
        return
    
    # Data from the PDF
    doctors_data = [
        {
            "name": "Dr. Ahmed Ali",
            "specialty": "Urology",
            "qualification": "MBChB, MSc, FRCS Uro",
            "experience_years": 15,
            "consultation_price": 800.0,
            "bio": "Dr. Ahmed Ali, a distinguished UK-trained Urological Surgeon, brings an exceptional level of expertise and dedication to the department of urology at Valiant Clinic City Walk Dubai. Renowned for his skills in managing complex urological conditions, Dr. Ahmed Ali combines cutting-edge medical solutions and knowledge with patient-centered approach.",
            "languages": ["English", "Arabic"],
            "profile_image": None,
            "conditions_treated": [
                "Vasectomy",
                "Aquablation",
                "Prostate Cancer Diagnostics and Management",
                "Bladder Cancer Treatment",
                "Overactive Bladder Syndrome Treatment"
            ],
            "specialties": [
                "Prostate Health",
                "Lower Urinary Tract Symptoms (LUTS)",
                "Urinary Tract Infections (UTIs)",
                "Kidney Stones"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Dr. Asif Naseem",
            "specialty": "General Practice",
            "qualification": "MRCGP, MBBS, BSc, BCAM",
            "experience_years": 12,
            "consultation_price": 600.0,
            "bio": "Dr. Asif Naseem is a renowned Private General Practitioner with extensive experience in preventive health, lifestyle medicine, and general practice. Based between Dubai and London, Dr. Naseem is dedicated to offering personalized healthcare services that focus on early detection, chronic disease management, and comprehensive health screenings.",
            "languages": ["English", "Urdu"],
            "profile_image": None,
            "conditions_treated": [
                "Prostate Health",
                "Allergic Rhinitis (Hay Fever)",
                "Digestive Disorders",
                "Respiratory Conditions",
                "Mental Health"
            ],
            "specialties": [
                "Health Screening",
                "Lifestyle Medicine",
                "GP Services",
                "Male & Female Health"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Dr. Fadi Jouhra",
            "specialty": "Cardiology",
            "qualification": "MD, MRCP, HFA",
            "experience_years": 18,
            "consultation_price": 900.0,
            "bio": "Dr. Fadi Jouhra is a highly esteemed international Consultant Cardiologist who specializes in the diagnosis and treatment of heart disease, hypertension, and cardiovascular risk management.",
            "languages": ["English", "Arabic", "French"],
            "profile_image": None,
            "conditions_treated": [
                "Heart Failure",
                "Chest Pain",
                "Shortness of breath",
                "Palpitations",
                "Cardiac Rehabilitation"
            ],
            "specialties": [
                "Cardiac Imaging",
                "Hypertension Management",
                "Cardiovascular Risk Assessments",
                "Implantable cardioverter defibrillator (ICD)"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Dr. Omar Sabri",
            "specialty": "Orthopedics",
            "qualification": "MBBCh, MS (Orth), FRCS (Tr&Orth)",
            "experience_years": 14,
            "consultation_price": 850.0,
            "bio": "Dr Sabri is an ortho specialist and Knee Surgeon Dubai, who specialises in pelvis and hip reconstruction procedures, including Arthroplasty, Fragility Fractures, Major Trauma Surgeries. He is one of the few Mako-trained (Robotic-Arm Assisted Makoplasty) surgeons for lower limb reconstruction including for bone and joint infection cases.",
            "languages": ["English", "Arabic"],
            "profile_image": None,
            "conditions_treated": [
                "Sports Injuries",
                "Fragility Fractures",
                "Major Trauma",
                "Chronic Knee Pain",
                "Hip Replacements"
            ],
            "specialties": [
                "Hip Replacement",
                "Complex Hip Replacement",
                "Knee Replacement",
                "Poly Trauma Injuries"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Dr. Annalisa Crudelli",
            "specialty": "Gastroenterology",
            "qualification": "MBChB, MSc, FRCS Uro",
            "experience_years": 10,
            "consultation_price": 750.0,
            "bio": "Dr. Annalisa Crudeli is a distinguished Consultant Gastroenterologist and Specialist Endoscopist based at The London Clinic, one of London's leading private hospitals. With over a decade of experience, she has built a strong reputation for her expertise in managing complex gastrointestinal conditions and her commitment to delivering exceptional patient care.",
            "languages": ["English", "Italian"],
            "profile_image": None,
            "conditions_treated": [
                "Crohn's Disease",
                "IBS & IBD",
                "Dyspepsia",
                "Peptic Ulcers",
                "Rectal Bleeding"
            ],
            "specialties": [
                "Colonoscopy & Bowel Cancer Prevention",
                "Inflammatory Bowel Disease (IBD)",
                "Functional Gastrointestinal Disorders"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Dr. Werner Beekman",
            "specialty": "Plastic Surgery",
            "qualification": "MBChB, MSc, FRCS Uro",
            "experience_years": 30,
            "consultation_price": 1200.0,
            "bio": "Dr. Werner H. Beekman is a visionary Plastic and Reconstructive Surgeon and Hand Surgeon who understands the dreams and desires of the men and women seeking transformative changes. With over 30 years of expertise in the field of plastic and aesthetic surgery, Dr. Beekman has earned a reputation for his exceptional skills and unwavering commitment to achieving stunning results.",
            "languages": ["English", "Dutch", "German"],
            "profile_image": None,
            "conditions_treated": [
                "Mommy Makeover",
                "Eyelid Surgery",
                "Face Lift/Neck Lift",
                "Hand Rejuvenation",
                "Brachioplasty"
            ],
            "specialties": [
                "Abdominoplasty",
                "Aesthetic Breast Surgery",
                "Body Contouring",
                "Liposuction/Lip Grafting"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
    ]
    
    # Generate example schedule for next 30 days
    for doctor in doctors_data:
        schedule = []
        
        # Start from tomorrow
        start_date = datetime.now().date() + timedelta(days=1)
        
        for day in range(30):
            current_date = start_date + timedelta(days=day)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Skip weekends (adjust as needed for UAE weekend)
            if current_date.weekday() in [4, 5]:  # Friday and Saturday
                continue
                
            # Create time slots from 9 AM to 5 PM in 30-minute intervals
            time_slots = []
            for hour in range(9, 17):
                for minute in [0, 30]:
                    start_time = f"{hour:02d}:{minute:02d}"
                    end_time = f"{hour:02d}:{minute+30:02d}" if minute == 0 else f"{hour+1:02d}:00"
                    
                    # Make some slots randomly unavailable
                    is_available = (day + hour + minute) % 5 != 0
                    
                    time_slots.append({
                        "start_time": start_time,
                        "end_time": end_time,
                        "is_available": is_available
                    })
            
            schedule.append({
                "date": date_str,
                "time_slots": time_slots
            })
        
        doctor["schedule"] = schedule
    
    await db.physicians.insert_many(doctors_data)
    logger.info(f"Seeded {len(doctors_data)} physicians successfully")

async def seed_treatments_data(db):
    """Seed treatments data from the provided PDF content."""
    # Check if treatments already exist
    existing_count = await db.treatments.count_documents({})
    if existing_count > 0:
        logger.info(f"{existing_count} treatments already exist, skipping")
        return
    
    # Data from the PDF
    treatments_data = [
        # Cardiology treatments
        {
            "name": "Cardiac Generator Replacement & Pacemaker Surgery",
            "specialty": "Cardiology",
            "description": "This procedure replaces the pacemaker's battery-powered generator, ensuring it continues to regulate heart rhythm effectively and prevent irregular heartbeats.",
            "price_range": {"min": 20000, "max": 35000},
            "duration_minutes": 120,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Cardiac Imaging",
            "specialty": "Cardiology",
            "description": "Cardiac imaging uses advanced technology to visualize the heart's structure and function, helping diagnose and monitor various cardiovascular conditions.",
            "price_range": {"min": 2000, "max": 8000},
            "duration_minutes": 60,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Cardiac Rehabilitation",
            "specialty": "Cardiology",
            "description": "Cardiac rehabilitation offers a comprehensive approach to recovery, helping patients regain strength, improve heart function, and reduce the risk of future heart problems.",
            "price_range": {"min": 3000, "max": 10000},
            "duration_minutes": 240,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        
        # Urology treatments
        {
            "name": "Benign Prostatic Hyperplasia (BPH) Surgery",
            "specialty": "Urology",
            "description": "This procedure improves bladder function and quality of life by addressing difficulties such as frequent urination, weak stream, and incomplete emptying.",
            "price_range": {"min": 15000, "max": 25000},
            "duration_minutes": 90,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Bladder Cancer Surgery",
            "specialty": "Urology",
            "description": "Bladder cancer surgery involves the removal of cancerous tissue from the bladder, ranging from minimally invasive tumor excision to partial or complete bladder removal in advanced cases.",
            "price_range": {"min": 25000, "max": 45000},
            "duration_minutes": 180,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Kidney Stone Removal Surgeries",
            "specialty": "Urology",
            "description": "Kidney stone removal surgeries use advanced techniques to break down or extract stones, relieving pain and restoring normal kidney function.",
            "price_range": {"min": 12000, "max": 20000},
            "duration_minutes": 120,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        
        # Orthopedics treatments
        {
            "name": "Hip Replacement",
            "specialty": "Orthopedics",
            "description": "Hip replacement surgery involves replacing the damaged hip joint with an artificial implant to relieve pain and improve mobility.",
            "price_range": {"min": 35000, "max": 60000},
            "duration_minutes": 150,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Knee Replacement",
            "specialty": "Orthopedics",
            "description": "Knee replacement surgery involves replacing the damaged knee joint with an artificial implant to relieve pain and improve mobility.",
            "price_range": {"min": 30000, "max": 55000},
            "duration_minutes": 150,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        
        # Gastroenterology treatments
        {
            "name": "Colonoscopy & Endoscopic Polypectomy",
            "specialty": "Gastroenterology",
            "description": "This procedure uses a flexible camera to inspect the colon and remove polyps or abnormal tissue, reducing the risk of colorectal cancer and improving digestive health.",
            "price_range": {"min": 4000, "max": 8000},
            "duration_minutes": 60,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Gastroscopy (Endoscopic Procedures)",
            "specialty": "Gastroenterology",
            "description": "Gastroscopy is an endoscopic procedure that uses a flexible camera to examine the stomach, esophagus, and duodenum, diagnosing conditions like ulcers or inflammation.",
            "price_range": {"min": 3500, "max": 7000},
            "duration_minutes": 45,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        
        # Plastic Surgery treatments
        {
            "name": "Abdominoplasty (Tummy Tuck)",
            "specialty": "Plastic Surgery",
            "description": "Abdominoplasty (Tummy Tuck) is a transformative body contouring procedure designed to remove excess abdominal skin, tighten underlying muscles, and create a firmer, flatter abdomen.",
            "price_range": {"min": 25000, "max": 40000},
            "duration_minutes": 180,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Breast Augmentation",
            "specialty": "Plastic Surgery",
            "description": "Breast Augmentation is a transformative procedure designed to enhance breast size, shape, and symmetry using implants or fat transfer techniques.",
            "price_range": {"min": 22000, "max": 35000},
            "duration_minutes": 120,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
    ]
    
    await db.treatments.insert_many(treatments_data)
    logger.info(f"Seeded {len(treatments_data)} treatments successfully")

async def seed_medical_packages_data(db):
    """Seed medical packages data from the provided PDF content."""
    # Check if packages already exist
    existing_count = await db.medical_packages.count_documents({})
    if existing_count > 0:
        logger.info(f"{existing_count} medical packages already exist, skipping")
        return
    
    # Data from the PDF
    packages_data = [
        {
            "name": "Valiant Signature Men's Health Checkup (40+)",
            "description": "A comprehensive health checkup for men aged 40 and above, including specialist consultation, essential tests, and lifestyle assessment.",
            "price": 3999.0,
            "duration_minutes": 180,
            "services": [
                "Initial Consultation",
                "Follow up",
                "Specialist Consultation",
                "Essential Tests",
                "Vitamin & Mineral Assessment",
                "Male Health",
                "Stool Tests",
                "Urine Tests",
                "X-ray",
                "Cardiac",
                "Ultrasound Scan",
                "Additional Diagnostics",
                "Lifestyle & Risk Assessment"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Valiant Signature Women's Health Checkup (40+)",
            "description": "A comprehensive health checkup for women aged 40 and above, including specialist consultation, essential tests, and lifestyle assessment.",
            "price": 4499.0,
            "duration_minutes": 200,
            "services": [
                "Initial Consultation",
                "Follow up",
                "Specialist Consultation",
                "Essential Tests",
                "Vitamin & Mineral Assessment",
                "Female Health",
                "Stool Tests",
                "Urine Tests",
                "X-ray",
                "Cardiac",
                "Ultrasound Scan",
                "Additional Diagnostics",
                "Lifestyle & Risk Assessment"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Platinum Health Checkup For Men Under 40",
            "description": "A comprehensive health checkup for men under 40, including specialist consultation, essential tests, and lifestyle assessment.",
            "price": 2999.0,
            "duration_minutes": 160,
            "services": [
                "Initial Consultation",
                "Follow up",
                "Specialist Consultation",
                "Essential Tests",
                "Vitamin & Mineral Assessment",
                "Men's Health",
                "Stool Tests",
                "Urine Tests",
                "X-Ray",
                "Cardiac",
                "Additional Diagnostics",
                "Lifestyle & Risk Assessment"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Healthy Heart Package",
            "description": "A preventive package designed to maintain heart health and detect early cardiovascular conditions.",
            "price": 1999.0,
            "duration_minutes": 120,
            "services": [
                "Lipid profile",
                "Blood pressure monitoring",
                "ECG and echocardiogram",
                "Cardiac stress test",
                "Consultation with a Family Medicine Specialist"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "name": "Comprehensive Cardiac Screening",
            "description": "A detailed evaluation of cardiovascular health for individuals at high risk.",
            "price": 5950.0,
            "duration_minutes": 240,
            "services": [
                "Lipid profile, BPM, ECG, and Echocardiagram",
                "Coronary CT angiogram",
                "24-hour Holter monitoring",
                "Advanced blood tests for cardiac markers",
                "Cardiologist consultation with follow-up"
            ],
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
    ]
    
    await db.medical_packages.insert_many(packages_data)
    logger.info(f"Seeded {len(packages_data)} medical packages successfully")

async def main():
    """Main function to seed all data."""
    if not MONGO_URI:
        logger.error("MONGO_URI environment variable is not set")
        return
    
    try:
        db = await connect_to_mongo()
        
        # Seed all data
        await seed_clinic_data(db)
        await seed_doctors_data(db)
        await seed_treatments_data(db)
        await seed_medical_packages_data(db)
        
        logger.info("Data seeding completed successfully")
    except Exception as e:
        logger.error(f"Error seeding data: {str(e)}")
    
if __name__ == "__main__":
    asyncio.run(main())