class Message: 
    role = None

    def __init__(self, content): 
        if self.role is None: 
            raise TypeError("Use NeuralNetworkMessage, HomosapiensMessage, AIMessage")
        if isinstance(content, str): 
            raise TypeError("Content must be a string")
        self.content = content

    def to_dict(self): 
        return {'role':self.role, 'content':self.content}

    def __eq__(self,other):
        return isinstance(other, Message) and self.to_dict() == other.to_dict()

    def __repr__(self): 
        text = self.content
        return f"{type(self).__name__}({text!r})"

class NeuralNetworkMessage(Message): 
    role = "system"

class HomosapiensMessage(Message): 
    role = "user"

class IntelligenceMessage(Message): 
    role = "assistant"

_BY_ROLE = {
    "system":NeuralNetworkMessage, 
    "user":HomosapiensMessage, 
    "assistant":IntelligenceMessage
}


def from_dict(d): 
    try: 
        return _BY_ROLE[d['role']](d['content'])
    except KeyError:
        raise ValueError(f"Bad message:{d!r}")

def to_dicts(messages): 
    """Accept a mix of Message objects and plain dicts -> list of dicts."""
    return [m.to_dict() if isinstance(m,Message) else dict(m) for m in messages]


def from_dicts(dicts): 
    return [from_dict(d) for d in dicts]
