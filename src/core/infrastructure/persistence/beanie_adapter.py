import abc
from typing import Any, List, Optional, Type, TypeVar, Generic
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

from src.core.repository import IRepository
from src.core.filters import FilterCriteria, Operator

T = TypeVar("T")
D = TypeVar("D", bound=Document)

class BeanieRepository(IRepository[T], Generic[T, D]):
    """Implementation of IRepository using Beanie and MongoDB."""
    
    def __init__(self, document_model: Type[D]):
        self.doc_model = document_model

    async def get(self, id: Any) -> Optional[T]:
        doc = await self.doc_model.get(id)
        return self._to_entity(doc) if doc else None

    async def find(self, criteria: Optional[FilterCriteria] = None) -> List[T]:
        query = self.doc_model.find_all()
        if criteria:
            query = self._apply_criteria(query, criteria)
        
        docs = await query.to_list()
        return [self._to_entity(doc) for doc in docs]

    async def count(self, criteria: Optional[FilterCriteria] = None) -> int:
        query = self.doc_model.find_all()
        if criteria:
            query = self._apply_criteria(query, criteria)
        return await query.count()

    async def add(self, entity: T) -> T:
        doc = self._to_document(entity)
        await doc.insert()
        return self._to_entity(doc)

    async def update(self, entity: T) -> T:
        doc = self._to_document(entity)
        await doc.save()
        return self._to_entity(doc)

    async def delete(self, id: Any) -> bool:
        doc = await self.doc_model.get(id)
        if doc:
            await doc.delete()
            return True
        return False

    @abc.abstractmethod
    def _to_entity(self, doc: D) -> T:
        """Convert a Beanie document to a domain entity."""
        pass

    @abc.abstractmethod
    def _to_document(self, entity: T) -> D:
        """Convert a domain entity to a Beanie document."""
        pass

    def _apply_criteria(self, query, criteria: FilterCriteria):
        """Map generic FilterCriteria to Beanie queries."""
        for criterion in criteria.criteria:
            field = criterion.field
            op = criterion.operator
            val = criterion.value
            
            if op == Operator.EQ:
                query = query.find({field: val})
            elif op == Operator.NEQ:
                query = query.find({field: {"$ne": val}})
            elif op == Operator.GT:
                query = query.find({field: {"$gt": val}})
            elif op == Operator.GTE:
                query = query.find({field: {"$gte": val}})
            elif op == Operator.LT:
                query = query.find({field: {"$lt": val}})
            elif op == Operator.LTE:
                query = query.find({field: {"$lte": val}})
            elif op == Operator.IN:
                query = query.find({field: {"$in": val}})
            elif op == Operator.NIN:
                query = query.find({field: {"$nin": val}})
            # Add LIKE/ILIKE using regex if needed
        
        if criteria.sort_by:
            sort_dir = "-" if criteria.descending else "+"
            query = query.sort(f"{sort_dir}{criteria.sort_by}")
        
        if criteria.limit:
            query = query.limit(criteria.limit)
        if criteria.offset:
            query = query.skip(criteria.offset)
            
        return query

class DatabaseManager:
    """Handles MongoDB connection and Beanie initialization."""
    
    def __init__(self, mongodb_url: str, db_name: str):
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db_name = db_name
        self.doc_models: List[Type[Document]] = []

    def register_model(self, model: Type[Document]):
        """Register a Beanie document model for initialization."""
        if model not in self.doc_models:
            self.doc_models.append(model)
            logger.debug(f"Registered document model: {model.__name__}")

    async def initialize(self):
        """Initialize Beanie with the registered models."""
        logger.info(f"Initializing Beanie for database: {self.db_name}...")
        await init_beanie(database=self.client[self.db_name], document_models=self.doc_models)
        logger.success("Beanie initialization complete.")
