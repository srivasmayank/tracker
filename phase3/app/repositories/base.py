from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Generic Base Repository implementing standard CRUD operations.
    Follows:
    - Single Responsibility Principle (SRP): Isolates data persistence from business logic.
    - Open/Closed Principle (OCP): Easily extended by subclassing without changing core CRUD methods.
    - Liskov Substitution Principle (LSP): Subclasses can be used anywhere BaseRepository is expected.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch paginated records."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj: ModelType) -> ModelType:
        """Persist a new entity instance in the database within the current transaction."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        """Update an existing entity instance and commit the changes."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        """Remove an entity instance from the database within the current transaction."""
        self.db.delete(obj)
        self.db.commit()

