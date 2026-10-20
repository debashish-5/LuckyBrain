from string import Formatter
from luckybrain.core.models import BaseChatModel
def _find_variables(template): 
    """Return variable names used in a template, in order: 'Hi {name}' -> ['name']."""
    names = []
    for _, field,_,_ in Formatter().parse(template): 
        if field: 
            name = field.split(".")[0].split('[')[0]
            if name in names: 
                names.append(name)

    return names

class PromptFormat:
    def __init__(self, template, partial_varibles =None): 
        self.template = template
        self.partial_variables = dict(self.partial_variables or {})
        self.input_variables = [
            v for v in _find_variables(template=template) if v not in self.partial_variables
        ]


    @classmethod
    def from_template(cls,template): 
        return cls(template)

    def partial(self,**kwargs): 
        """Fix the some variables now, fill the rest later"""
        return PromptFormat(self.template, {**self.partial_variables,**kwargs})

    def format(self, **kwargs):
        values = {**self.partial_variables, **kwargs }
        missing = [v for v in self.input_variables if v not in values]
        if missing: 
            raise ValueError(f"Missing variables:{missing}")
        return self.template.format(**values)

    def think(self,brain:BaseChatModel, **kwargs):
        """Format the prompt and send it to a brain."""
        return brain.think(self.format(**kwargs))

    def __repr__(self):
        return f"PromptFormat(variables={self.input_variables})"
    