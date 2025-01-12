from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta

class CustomBase:
    """
    Custom base class for SQLAlchemy models with additional utility methods
    """
    __abstract__ = True

    @classmethod
    def create(cls, **kwargs):
        """
        Create a new instance of the model
        
        :param kwargs: Keyword arguments to initialize the model
        :return: New model instance
        """
        return cls(**kwargs)

    def update(self, **kwargs):
        """
        Update model instance attributes
        
        :param kwargs: Keyword arguments to update
        :return: Updated model instance
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def to_dict(self):
        """
        Convert model instance to dictionary
        
        :return: Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

# Create base with custom functionality
Base: DeclarativeMeta = declarative_base(cls=CustomBase)
