from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..jsgui import Controller


class View(ABC):

    def __init__(self, controller: 'Controller'):
        self.controller = controller

    @abstractmethod
    def mainloop(self):
        pass

    @abstractmethod
    def paint(self):
        pass

    @abstractmethod
    def popup_showerror(self, title, msg):
        pass
