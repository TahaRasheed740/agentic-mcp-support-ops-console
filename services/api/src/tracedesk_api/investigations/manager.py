from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine

from tracedesk_api.config import Settings
from tracedesk_api.investigations.model import AnthropicInvestigationModel, InvestigationModel
from tracedesk_api.investigations.repository import InvestigationRepository
from tracedesk_api.investigations.workflow import InvestigationWorkflow
from tracedesk_api.mcp_layer.contracts import AuthorizationContext
from tracedesk_api.mcp_layer.gateway import MCPGateway


class InvestigationManager:
    def __init__(self, engine: AsyncEngine, settings: Settings) -> None:
        self.engine = engine
        self.settings = settings
        self.tasks: dict[str, asyncio.Task[None]] = {}

    async def create(
        self,
        case_id: str,
        authorization: AuthorizationContext,
        model: InvestigationModel | None = None,
    ) -> str:
        repository = InvestigationRepository(self.engine)
        investigation_id = await repository.create(
            case_id=case_id,
            session_id=authorization.session_id,
            persona_id=authorization.persona_id,
            router_model=self.settings.claude_router_model,
            investigator_model=self.settings.claude_investigator_model,
        )
        workflow = InvestigationWorkflow(
            repository=repository,
            gateway=MCPGateway(self.settings),
            model=model or AnthropicInvestigationModel(self.settings),
            settings=self.settings,
        )
        task = asyncio.create_task(
            workflow.run(investigation_id, case_id, authorization),
            name=f"investigation-{investigation_id}",
        )
        self.tasks[investigation_id] = task
        task.add_done_callback(lambda _task: self.tasks.pop(investigation_id, None))
        return investigation_id

    async def shutdown(self) -> None:
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self.tasks.clear()
