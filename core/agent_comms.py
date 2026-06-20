"""
Agent-to-Agent Communication Router for Auto Makah.

Agents are async callables that exchange messages, deliberate in groups,
and chain-execute in pipelines — all with per-conversation message history.
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence

# ── type aliases ─────────────────────────────────────────────────────

Agent = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
"""An agent is an async function that receives a message dict and returns a result dict."""


# ── data structures ──────────────────────────────────────────────────

@dataclass
class Message:
    """A single message in an agent-to-agent conversation."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    conversation_id: str = ""
    from_agent: str = ""
    to_agent: str = ""
    content: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "from": self.from_agent,
            "to": self.to_agent,
            "content": self.content,
            "timestamp": self.timestamp,
        }


@dataclass
class Conversation:
    """Ordered message history for a single conversation thread."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    topic: str = ""
    messages: List[Message] = field(default_factory=list)

    def add(self, msg: Message) -> None:
        msg.conversation_id = self.id
        self.messages.append(msg)

    @property
    def transcript(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self.messages]


# ── router ───────────────────────────────────────────────────────────

class AgentRouter:
    """
    Routes messages between agents, maintains conversation history, and
    orchestrates multi-agent deliberation and chain execution.

    Usage::

        router = AgentRouter()

        # register async agent functions
        router.register("researcher", researcher_agent)
        router.register("writer", writer_agent)

        # point-to-point
        resp = await router.send_message("researcher", "writer", "summarise this")

        # broadcast
        responses = await router.broadcast("owner", {"action": "status_check"})

        # deliberation → consensus
        consensus = await router.deliberate(
            ["researcher", "writer", "editor"],
            topic="What is the best architecture for this app?",
        )

        # chain  A → B → C
        final = await router.chain_execute(
            ["researcher", "writer", "editor"],
            initial_input={"query": "explain multi-tenancy"},
        )
    """

    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}
        self._conversations: Dict[str, Conversation] = {}
        self._history: List[Message] = []  # global audit log

    # ── registry ─────────────────────────────────────────────────────

    def register(self, name: str, agent: Agent) -> None:
        """Register an async agent function under *name*."""
        self._agents[name] = agent

    def unregister(self, name: str) -> bool:
        """Remove an agent. Returns ``False`` if unknown."""
        return self._agents.pop(name, None) is not None

    def list_agents(self) -> List[str]:
        """Return registered agent names."""
        return list(self._agents.keys())

    def is_registered(self, name: str) -> bool:
        return name in self._agents

    # ── messaging ────────────────────────────────────────────────────

    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message: Any,
        *,
        conversation_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send *message* from one agent to another.

        Args:
            from_agent: Name of the sending agent.
            to_agent: Name of the receiving agent.
            message: Message payload (string, dict — whatever the agent expects).
            conversation_id: If given, appends to that thread; otherwise
                starts a new conversation.

        Returns:
            The receiving agent's response dict, or ``None`` if *to_agent*
            is not registered.
        """
        if to_agent not in self._agents:
            return None

        msg = Message(from_agent=from_agent, to_agent=to_agent, content=message)

        # record in conversation
        conv = self._get_or_create_conversation(conversation_id, topic="direct-message")
        conv.add(msg)
        self._history.append(msg)

        # invoke target agent
        payload: Dict[str, Any] = {
            "from": from_agent,
            "message": message,
            "history": conv.transcript,
        }
        result = await self._agents[to_agent](payload)

        # record response as a follow-up message
        reply = Message(
            from_agent=to_agent,
            to_agent=from_agent,
            content=result,
        )
        conv.add(reply)
        self._history.append(reply)

        return result

    async def broadcast(
        self,
        from_agent: str,
        message: Any,
        *,
        exclude: Optional[Sequence[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Send *message* to every registered agent except *from_agent*
        (and any names in *exclude*).

        Returns:
            A dict mapping agent name → response.
        """
        skip = {from_agent} | (set(exclude) if exclude else set())
        targets = [n for n in self._agents if n not in skip]
        futures = {
            name: self.send_message(from_agent, name, message)
            for name in targets
        }
        results = await asyncio.gather(*futures.values(), return_exceptions=True)
        return {
            name: (res if not isinstance(res, BaseException) else {"error": str(res)})
            for name, res in zip(targets, results)
        }

    # ── deliberation ─────────────────────────────────────────────────

    async def deliberate(
        self,
        agents_list: Sequence[str],
        topic: str,
        *,
        rounds: int = 3,
    ) -> Dict[str, Any]:
        """
        Have *agents_list* discuss *topic* over *rounds* and reach consensus.

        Each round every agent sees the transcript so far and contributes.
        After the final round the last agent's response is returned as the
        consensus payload.

        Args:
            agents_list: Ordered list of agent names to deliberate.
            topic: The discussion topic.
            rounds: How many full passes over the agent list to perform.

        Returns:
            Consensus dict (the last agent's output after the final round).
        """
        conv = self._get_or_create_conversation(topic=topic)
        last_result: Dict[str, Any] = {}

        for rnd in range(1, rounds + 1):
            for agent_name in agents_list:
                if agent_name not in self._agents:
                    continue

                payload: Dict[str, Any] = {
                    "from": "deliberation",
                    "message": topic,
                    "round": rnd,
                    "history": conv.transcript,
                    "instruction": f"Round {rnd}/{rounds}. Contribute your view on: {topic}",
                }
                result = await self._agents[agent_name](payload)
                last_result = result

                msg = Message(from_agent=agent_name, to_agent="group", content=result)
                conv.add(msg)
                self._history.append(msg)

        return {
            "consensus": last_result,
            "topic": topic,
            "rounds": rounds,
            "participants": [a for a in agents_list if a in self._agents],
            "transcript": conv.transcript,
        }

    # ── chain execution ──────────────────────────────────────────────

    async def chain_execute(
        self,
        agents_chain: Sequence[str],
        input_data: Any,
        *,
        merge_history: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute agents in a pipeline: A → B → C.

        The output of agent *N* becomes the ``message`` field for agent *N+1*.
        The final agent's output is returned.

        Args:
            agents_chain: Ordered list of agent names.
            input_data: Initial input for the first agent.
            merge_history: If ``True``, each downstream agent sees the full
                transcript so far.

        Returns:
            The final agent's response.
        """
        conv = self._get_or_create_conversation(topic="chain-execute")
        current = input_data
        result: Dict[str, Any] = {}

        for agent_name in agents_chain:
            if agent_name not in self._agents:
                continue

            payload: Dict[str, Any] = {
                "from": "chain",
                "message": current,
                "history": conv.transcript if merge_history else [],
            }
            result = await self._agents[agent_name](payload)
            current = result

            msg = Message(from_agent=agent_name, to_agent="chain", content=result)
            conv.add(msg)
            self._history.append(msg)

        return result

    # ── conversation helpers ─────────────────────────────────────────

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Return a conversation by id, or ``None``."""
        return self._conversations.get(conversation_id)

    def list_conversations(self) -> List[Conversation]:
        return list(self._conversations.values())

    def get_history(self, limit: Optional[int] = None) -> List[Message]:
        """Return global message log, newest last."""
        return self._history[-limit:] if limit else self._history[:]

    # ── internal ─────────────────────────────────────────────────────

    def _get_or_create_conversation(
        self,
        conversation_id: Optional[str] = None,
        *,
        topic: str = "",
    ) -> Conversation:
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]
        conv = Conversation(id=conversation_id or uuid.uuid4().hex[:8], topic=topic)
        self._conversations[conv.id] = conv
        return conv
