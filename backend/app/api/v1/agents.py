from fastapi import APIRouter

from backend.app.agents.protocol import get_capability_registry

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("/capabilities")
async def list_capabilities() -> dict:
    registry = get_capability_registry()
    caps = registry.get_all()
    return {
        "capabilities": [cap.model_dump() for cap in caps],
        "total": len(caps),
    }


@router.get("/capabilities/{agent_name}")
async def get_agent_capability(agent_name: str) -> dict:
    registry = get_capability_registry()
    cap = registry.get(agent_name)
    if not cap:
        return {"error": f"Agent {agent_name} not found"}
    return cap.model_dump()


@router.get("/agents/for-intent/{intent}")
async def find_agents_for_intent(intent: str) -> dict:
    registry = get_capability_registry()
    caps = registry.find_agent_for_intent(intent)
    return {
        "intent": intent,
        "agents": [cap.name for cap in caps],
        "total": len(caps),
    }
