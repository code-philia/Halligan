import inspect
from textwrap import indent
from typing import Any, Callable, get_type_hints


class Tool:
    def __init__(self, handler: Callable[..., Any] | property) -> None:
        self.handler = handler

        if isinstance(handler, property):
            self.owner = handler.fget.__qualname__.split(".")[0]
            self.name = handler.fget.__name__
            self.parameters = {}
            self.return_type = self.handler.fget.__annotations__.get('return', None)
            
        elif isinstance(handler, Callable):
            qualname = handler.__qualname__.split(".")
            self.owner = None if len(qualname) == 1 else qualname[0]
            self.name = handler.__name__
            self.parameters = {k: self._format_type_hint(v) for k, v in get_type_hints(self.handler).items()}
            self.parameters.pop("return", None)
            self.parameters.pop("self", None)
            self.return_type = self.handler.__annotations__.get('return', None)

        else:
            raise TypeError("Tool handler must be a property or callable.")
          
        self.docs = self._get_docs()

    def __str__(self) -> str:
        return self.docs
    
    def _format_type_hint(self, type_hint):
        """
        Formats the type hint
        1. Recursively handles generics (e.g., List[List[int]], Dict[str, int])
        2. Excluding module names for classes (e.g., module.submodule.Class)
        """
        if type_hint is type(None):
            return None
        
        elif hasattr(type_hint, '__origin__'):
            origin, args = type_hint.__origin__, type_hint.__args__
            base_name = origin.__name__
            if args:
                args_names = [self._format_type_hint(arg) for arg in args]
                return f"{base_name}[{', '.join(args_names)}]"
            return base_name
        
        elif hasattr(type_hint, '__name__'):
            # Handle non-generic types (e.g., int, str)
            return type_hint.__name__
        
        return str(type_hint)
        
    def _get_docs(self) -> str:
        """
        Convert tool (function) into a string that can be inserted into prompt.
        String representation formats:

        1. Class property
            - Class.property -> ReturnType
            - Example: Frame.image -> PIL.Image.Image

        2. Class method
            - Class.method(parameters) -> ReturnType
            - Example: Frame.get_element(location: str, description: str) -> Element

        3. Function
            - function(parameters) -> ReturnType
            - Example: click(target: Element | Frame) -> None
        """
        tool_name = f"{self.owner}.{self.name}" if self.owner else self.name
        return_type = f" -> {self.return_type}:" if self.return_type else ""

        parameters = ""
        if isinstance(self.handler, Callable):
            parameters = ", ".join([f"{k}: {v}" if v is not None else f"{k}" for k, v in self.parameters.items()])
            parameters = f"({parameters})" if parameters else "()"
        
        docstring = inspect.cleandoc(self.handler.__doc__ or "")
        docstring = indent(f"\n{docstring}", "\t") if docstring else ""

        result = f"{tool_name}{parameters}{return_type}{docstring}"
        return result


class Toolkit:
    def __init__(self, tools: list[Callable | property], dependencies: dict[str, Any]) -> None:
        """
        Create a new toolkit with a set of `tools` and `dependencies`.

        Args:
            tools (list[Tool]): A list of callable objects (functions, class methods, etc.) or properties.
            dependencies (dict[str, Any]): A dictionary of dependencies (global variables or other objects) 
                                        to be made available for dynamic execution with `exec()`.
        """
        self.tools = [Tool(tool) for tool in tools]
        self.dependencies = dependencies