from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING
import os
from typing import List, Optional, Dict, Any
from models import Consultation, Message, ConsultationStatus
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.mongo_url = os.environ['MONGO_URL']
        self.db_name = os.environ['DB_NAME']
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            await self._create_indexes()
            logger.info("Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()

    async def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Consultations collection indexes
            consultations_indexes = [
                IndexModel([("session_token", ASCENDING)], unique=True),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("updated_at", DESCENDING)])
            ]
            await self.db.consultations.create_indexes(consultations_indexes)

            # Messages collection indexes
            messages_indexes = [
                IndexModel([("consultation_id", ASCENDING), ("timestamp", ASCENDING)]),
                IndexModel([("consultation_id", ASCENDING)]),
                IndexModel([("timestamp", DESCENDING)])
            ]
            await self.db.messages.create_indexes(messages_indexes)

            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    # Consultation methods
    async def create_consultation(self, consultation: Consultation) -> str:
        """Create a new consultation"""
        try:
            consultation_dict = consultation.dict()
            result = await self.db.consultations.insert_one(consultation_dict)
            return consultation.id
        except Exception as e:
            logger.error(f"Failed to create consultation: {e}")
            raise

    async def get_consultation(self, consultation_id: str) -> Optional[Consultation]:
        """Get consultation by ID"""
        try:
            consultation_data = await self.db.consultations.find_one({"id": consultation_id})
            if consultation_data:
                return Consultation(**consultation_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get consultation: {e}")
            return None

    async def get_consultation_by_token(self, session_token: str) -> Optional[Consultation]:
        """Get consultation by session token"""
        try:
            consultation_data = await self.db.consultations.find_one({"session_token": session_token})
            if consultation_data:
                return Consultation(**consultation_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get consultation by token: {e}")
            return None

    async def update_consultation(self, consultation_id: str, updates: Dict[str, Any]) -> bool:
        """Update consultation"""
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.db.consultations.update_one(
                {"id": consultation_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update consultation: {e}")
            return False

    async def update_consultation_status(self, consultation_id: str, status: ConsultationStatus) -> bool:
        """Update consultation status"""
        return await self.update_consultation(consultation_id, {"status": status})

    # Message methods
    async def add_message(self, message: Message) -> str:
        """Add message to consultation"""
        try:
            message_dict = message.dict()
            await self.db.messages.insert_one(message_dict)
            
            # Update consultation's updated_at timestamp
            await self.update_consultation(message.consultation_id, {})
            
            return message.id
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise

    async def get_messages(self, consultation_id: str, limit: int = 100) -> List[Message]:
        """Get messages for consultation"""
        try:
            cursor = self.db.messages.find(
                {"consultation_id": consultation_id}
            ).sort("timestamp", ASCENDING).limit(limit)
            
            messages = []
            async for message_data in cursor:
                messages.append(Message(**message_data))
            return messages
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []

    async def get_recent_messages(self, consultation_id: str, count: int = 10) -> List[Message]:
        """Get recent messages for consultation"""
        try:
            cursor = self.db.messages.find(
                {"consultation_id": consultation_id}
            ).sort("timestamp", DESCENDING).limit(count)
            
            messages = []
            async for message_data in cursor:
                messages.append(Message(**message_data))
            return list(reversed(messages))  # Return in chronological order
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []

    # Statistics methods
    async def get_consultation_count(self) -> int:
        """Get total number of consultations"""
        try:
            return await self.db.consultations.count_documents({})
        except Exception as e:
            logger.error(f"Failed to get consultation count: {e}")
            return 0

    async def get_active_consultations_count(self) -> int:
        """Get number of active consultations"""
        try:
            return await self.db.consultations.count_documents({
                "status": {"$in": ["active", "collecting_info", "analyzing"]}
            })
        except Exception as e:
            logger.error(f"Failed to get active consultations count: {e}")
            return 0

    async def cleanup_old_consultations(self, days: int = 30):
        """Cleanup old consultations (optional maintenance)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = await self.db.consultations.delete_many({
                "created_at": {"$lt": cutoff_date},
                "status": "completed"
            })
            logger.info(f"Cleaned up {result.deleted_count} old consultations")
        except Exception as e:
            logger.error(f"Failed to cleanup old consultations: {e}")

# Global database instance
db_manager = DatabaseManager()