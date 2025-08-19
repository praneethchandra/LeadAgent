"""Observer pattern implementation for event handling."""

from abc import ABC, abstractmethod
from typing import Any, List


class Observer(ABC):
    """Abstract observer interface."""
    
    @abstractmethod
    async def update(self, subject: 'Subject', event_type: str, data: Any) -> None:
        """Handle notification from subject.
        
        Args:
            subject: Subject that sent the notification
            event_type: Type of event
            data: Event data
        """
        pass


class Subject:
    """Subject that can be observed."""
    
    def __init__(self) -> None:
        """Initialize subject."""
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer) -> None:
        """Attach an observer.
        
        Args:
            observer: Observer to attach
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        """Detach an observer.
        
        Args:
            observer: Observer to detach
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    async def notify(self, event_type: str, data: Any = None) -> None:
        """Notify all observers of an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        for observer in self._observers:
            try:
                await observer.update(self, event_type, data)
            except Exception:
                # Continue notifying other observers even if one fails
                pass
