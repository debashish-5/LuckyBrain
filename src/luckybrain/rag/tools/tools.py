import inspect
import json
from typing import Literal, Union, get_args, get_origin,get_type_hints


TYPE_MAP = {
    str:"string",int:"integer",float:"float",bool:"boolean",list:"array",dict:"object"
}

def _json_schema(hint): 
    """Python type hint -> JSON schema fragment."""
    origin = get_origin(hint)
    if origin is Literal: 
        values = list(get_args(hint))
        return {
            "types":TYPE_MAP.get(type(values[0]), "string"), 
            "enum":values
        }
    if origin is Union: 
        args = [a for a in get_args(hint) if a is not type(None)]
        if len(args) == 1:
            return _json_schema(args[0])
        return {}

    if origin is list or hint is list: 
        args = get_args(hint)
        schema = {"type":"array"}
        if args: 
            schema['items'] = _json_schema(args[0])
        return schema
    return {'type':TYPE_MAP.get(hint,"string")}


def _parse_docstring(func): 
    """Return (description, {param:text}) from a Google-style docstring."""
    doc = inspect.getdoc(func) or ""
    head, _, args_part = doc.partition("Args:")
    description = "".join(head.split())
    params, current = {}, None
    for line in args_part.splitlines():
        if not line.strip(): 
            continue
        if line.startswith((" ","\t")) and ":" in line and not line.startswith("       "):
            name,_,text = line.strip().partition(":")
            current = name.split("(")[0].strip()
            params[current] = text.strip()
        elif current and line.startswith((" ", "\t")): 
            params[current] += " " + line.strip()     #wrapped line
        else: 
            break  # next section (Return:...)
    return description,params


class Tool:
    def __init__(self, func, name = None, description = None) : 
        self.func = func
        self.name = name or func.__name__
        doc_description, self.param_docs = _parse_docstring(func=func)
        self.description = description or doc_description
        if not self.description: 
            raise ValueError(f"Tool '{self.name}' needs a docstring or description = ...")
        self._sig = inspect.signature(func)
        self._hints = get_type_hints(func)

    @property
    def parameters(self): 
        props,required = {}, []
        for pname, p in self._sig.parameters.items(): 
            if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD): 
                continue
            schema = _json_schema(self._hints.get(pname,str))
            if pname in self.param_docs: 
                schema['description'] = self.param_docs[pname]
            props[pname] = schema
            if p.default is p.empty: 
                required.append(pname)
        return {
            "type":"object", 
            "properties":props, 
            "required":required
        }

    @property
    def schema(self):
        """Openai/Groq tool format."""
        return {
            "type":"function",
            "function":{
                "name":self.name,
                "description":self.description, 
                "parameters":self.parameters,
            }
        }


    def _coerce(self,name,value): 
        """Model sometimes send "5" for an int. Convert simple cases."""
        hint = self._hints.get(name)
        try: 
            if hint is int and not isinstance(value, float): 
                return int(value)
            if hint is float: 
                return float(value)
            if hint is bool and isinstance(value,str): 
                return value.strip().lower() in ("true", "1","yes")
        except (TypeError, ValueError): 
            raise ValueError(f"'{name}' must be {hint.__name__}, got {value!r}")
        
        return value


    def pull(self,args=None, **kwargs): 
        """Run the tool with a dict (from the model) or keyword arguments."""
        args = {**(args or {}), **kwargs}
        allowed = set(self.parameters['properties'])
        unknown = set(args) - allowed
        if unknown:
            raise ValueError(f"Unknown arguments: {sorted(unknown)}")
        missing = [r for r in self.parameters['required'] if r not in args]
        if missing: 
            raise ValueError(f"Missing arguments:{missing}")
        args = {k: self._coerce(k, v) for k, v in args.items()}
        return self.func(**args)

    