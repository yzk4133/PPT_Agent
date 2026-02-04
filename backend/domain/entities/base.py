"""
Base classes for Domain-Driven Design

Provides Entity, ValueObject, and Serializable base classes
for all domain models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any


class Entity(ABC):
    """
    Base class for all entities

    Entities have identity and are distinguished by their ID,
    not by their attributes.
    """

    pass


class ValueObject(ABC):
    """
    Base class for all value objects

    Value objects are immutable, have no identity, and are
    defined by their attributes. Two value objects with the
    same attributes are considered equal.
    """

    def __eq__(self, other):
        """Value objects are equal if all attributes are equal"""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self):
        """Value objects with same attributes have same hash"""
        return hash(tuple(sorted(self.__dict__.items())))


class Serializable(ABC):
    """
    Mixin for serialization support

    Provides to_dict() and from_dict() methods for domain models.
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation

        Returns:
            Dictionary representation of the object
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Create instance from dictionary

        Args:
            data: Dictionary representation

        Returns:
            Instance of the class
        """
        pass


class AggregateRoot(Entity):
    """
    Base class for aggregate roots

    Aggregate roots are the root of an aggregate hierarchy.
    They are the only objects that can be directly accessed
    from outside the aggregate.
    """

    pass
