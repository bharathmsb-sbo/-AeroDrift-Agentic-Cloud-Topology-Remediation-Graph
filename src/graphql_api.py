
import strawberry
from strawberry.scalars import JSON
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from src.state_persistence import StatePersistence
from src.historical_state import HistoricalState


@strawberry.type
class Query:

    @strawberry.field
    def health(self) -> str:
        return "AeroDrift GraphQL API is running"

    @strawberry.field
    def saved_state(self) -> JSON:
        return StatePersistence().load_state()

    @strawberry.field
    def historical_states(self) -> JSON:
        return HistoricalState().get_all_states()


schema = strawberry.Schema(query=Query)

app = FastAPI(title="AeroDrift GraphQL API")

app.include_router(
    GraphQLRouter(schema),
    prefix="/graphql"
)
