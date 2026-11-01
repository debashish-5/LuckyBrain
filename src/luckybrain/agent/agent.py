import json 
from luckybrain.core.models import BaseChatModel
EMPTY_REPLY = "(empty reply)"

class Agent: 
    """Tool-using agent that works with any chat model having .generate(messages).

    Each step the model replies with ONE JSON object:
      {"thought": "...", "tool": "name", "args": {...}}   -> the agent runs the tool
      {"final": "answer"}                                  -> the agent returns the answer
    """

    def __init__(self, 
                 brain: BaseChatModel, 
                 tools: list | None = None, 
                 instruction: str | None = None, 
                 max_steps: int | None = None, 
                 verbose: bool | None = False, 
                 confirm = None, 
                 max_observation_char: int | None = 4000
    ) : 

        self.tools = {}
        for t in tools: 
            if t.name in self.tools: 
                raise ValueError(f"Duplicate tool name: {t.name!r}")
            self.tools[t.name] = t

        self.brain = brain
        self.max_steps = max_steps
        self.verbose = verbose
        self.confirm = confirm
        self.max_observation_char = max_observation_char

        self._system = {'role':'system','content':self._build_prompt(instruction)}

        self.messages = [dict[self._system]]
        self.steps = []


    def _build_prompt(self,instructions): 
        tool_lines = "\n".join(
            f'{t.name}: {t.description} \n parameters: {json.dumps(t.parameters)}'
            for t in self.tools.values()
        )
        prompt = (

        )

        prompt = (
            "You are an agent that can use tools to help the user.\n\n"
            f"Available tools:\n{tool_lines}\n\n"
            "Reply with exactly ONE JSON object and nothing else.\n"
            'To use a tool: {"thought": "why", "tool": "<tool name>", "args": {...}}\n'
            'To answer the user: {"final": "<your answer>"}\n\n'
            "Rules:\n"
            "- Use a tool only when you need it. Never invent tool results.\n"
            "- After a tool call you receive an Observation. Use it for your next step.\n"
            "- If a tool returns an error, fix the arguments or try another approach.\n"
            "- Put your whole answer to the user inside the \"final\" field."
        )
        return f"{instructions.strip()}\n\n{prompt}" if instructions.strip() else prompt



    def run(self,question): 
        if not question.strip(): 
            raise ValueError("Question must not be empty")
        self.steps = []
        self.messages.append({'role':'user','content':question})
        bad_replies = 0

        for step in range(1,self.max_steps + 1): 
            reply = self._ask()
            action = self._parse(reply)

            if action is None:
                if "{" not in reply or reply != EMPTY_REPLY: 
                    return reply.strip()
                bad_replies += 1

                if bad_replies >= 2: 
                    return reply.strip()
                self._say('Your reply was not valid. Reply with ONE JSON object: '
                            '{"tool": "...", "args": {...}} or {"final": "..."}')
                continue

        bad_replies = 0 

        if 'final' in action: 
            return str(action['final'])

        observation = self._call_tool(action)

        self.steps.append({
            "step":step, 
            "tool":action.get("tool"),
            "args":action.get('args'), 
            'observation':observation
        })

        if self.verbose:
            print(f'[INFO] [step{step}] {action.get('tool')} ({action.get('args')}) -> {observation[:200]}')


        #out of stps . lets asking the best answer so far
        self._say('You are out of steps. Give your best final answer now as {"final": "..."}')
        reply = self._ask()
        action = self._parse(reply)

        return str(action['final']) if action and 'final' in action else reply.strip()


    def reset(self):
        """Forgot the conversation."""
        self.messages = [dict(self._system)]
        self.steps = []


    def _ask(self):
        reply = (self.brain.generate(self.messages) or "").strip() or EMPTY_REPLY
        self.messages.append({
            'role':'assistant', 
            'content':reply
        })

        return reply

    def say(self,text): 
        self.messages.append({'role':'user','content':text})

    