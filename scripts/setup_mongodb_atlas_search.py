#!/usr/bin/env python3
"""
Script to set up MongoDB Atlas Search indexes for hybrid search functionality.
This enables powerful text search capabilities for the chatbot agent.

In a production environment, these indexes would be created through the MongoDB Atlas
UI or using the Atlas Administration API. This script simulates that setup.
"""

import asyncio
import motor.motor_asyncio
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get MongoDB connection string from environment variable
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = "clinic_db"

SEARCH_INDEXES = {
    "clinic_info": {
        "name": "clinic_info_search",
        "definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                    "name": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "description": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "mission": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "vision": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "address": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    }
                }
            }
        }
    },
    "physicians": {
        "name": "physicians_search",
        "definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                    "name": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "specialty": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "bio": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "conditions_treated": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "specialties": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "languages": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    }
                }
            }
        }
    },
    "treatments": {
        "name": "treatments_search",
        "definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                    "name": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "specialty": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "description": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    }
                }
            }
        }
    },
    "medical_packages": {
        "name": "medical_packages_search",
        "definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                    "name": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "description": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    },
                    "services": {
                        "type": "string",
                        "analyzer": "lucene.standard"
                    }
                }
            }
        }
    }
}

async def connect_to_mongo():
    """Connect to MongoDB Atlas."""
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Verify the connection is successful
        await client.admin.command('ping')
        logger.info("Connected to MongoDB Atlas successfully")
        
        return db, client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def create_search_indexes(db, client):
    """Create Atlas Search indexes for various collections."""
    try:
        for collection_name, index_info in SEARCH_INDEXES.items():
            logger.info(f"Setting up search index for collection: {collection_name}")
            
            # In a real implementation, we would use the Atlas Administration API here
            # Since we don't have direct access, we'll simulate the creation with a message
            
            # Check if collection has documents (required for index creation)
            count = await db[collection_name].count_documents({})
            if count == 0:
                logger.warning(f"Collection {collection_name} is empty. Cannot create search index on empty collection.")
                continue
                
            # Display the index definition that would be created
            logger.info(f"Would create index '{index_info['name']}' on collection '{collection_name}' with definition:")
            logger.info(json.dumps(index_info['definition'], indent=2))
            
            logger.info(f"NOTE: In production, create this index in the MongoDB Atlas UI or use the Administration API.")
            
    except Exception as e:
        logger.error(f"Error creating search indexes: {str(e)}")
        raise

async def main():
    """Main function to set up all search indexes."""
    if not MONGO_URI:
        logger.error("MONGO_URI environment variable is not set")
        return
    
    try:
        db, client = await connect_to_mongo()
        await create_search_indexes(db, client)
        logger.info("Search index setup completed successfully")
    except Exception as e:
        logger.error(f"Error setting up search indexes: {str(e)}")
    finally:
        if 'client' in locals():
            client.close()
    
if __name__ == "__main__":
    asyncio.run(main())