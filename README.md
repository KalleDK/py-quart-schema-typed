# Quart Schema Typed

## Example

```python
app = Quart(__name__)

routes = RouteMgr(app)


@routes.get("/person", tags="HR")
async def list_persons(
    query_args: PersonQuery,
) -> tuple[list[Person], Literal[HTTPStatus.OK]] | tuple[APIError, Literal[HTTPStatus.BAD_REQUEST]]:
    ...
```
