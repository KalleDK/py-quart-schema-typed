import dataclasses
from http import HTTPStatus
from typing import Literal

from quart import Quart

from quart_schema_typed import RouteMgr


@dataclasses.dataclass
class Employed:
    company: str
    position: str


@dataclasses.dataclass
class Unemployed:
    reason: str


@dataclasses.dataclass
class Person:
    id: int
    name: str
    age: int
    employment: Employed | Unemployed


@dataclasses.dataclass
class CreatePersonPayload:
    name: str
    age: int
    employment: Employed | Unemployed


@dataclasses.dataclass
class PersonQuery:
    min_age: int | None = None
    max_age: int | None = None


@dataclasses.dataclass
class APIError:
    code: int
    message: str


app = Quart(__name__)

routes = RouteMgr(app)


@routes.get("/person", tags="HR")
async def list_persons(
    query_args: PersonQuery,
) -> tuple[list[Person], Literal[HTTPStatus.OK]] | tuple[APIError, Literal[HTTPStatus.BAD_REQUEST]]:
    if query_args.min_age is not None and query_args.min_age < 0:
        return APIError(code=400, message="min_age must be a positive integer"), HTTPStatus.BAD_REQUEST
    if query_args.max_age is not None and query_args.max_age < 0:
        return APIError(code=400, message="max_age must be a positive integer"), HTTPStatus.BAD_REQUEST
    if query_args.min_age is not None and query_args.max_age is not None and query_args.min_age > query_args.max_age:
        return APIError(code=400, message="min_age cannot be greater than max_age"), HTTPStatus.BAD_REQUEST

    persons = [Person(id=1, name="Dummy", age=30, employment=Employed(company="Company", position="Position"))]

    persons = [p for p in persons if query_args.min_age is None or p.age >= query_args.min_age]
    persons = [p for p in persons if query_args.max_age is None or p.age <= query_args.max_age]

    return persons, HTTPStatus.OK


@routes.get("/person/<name>", tags="HR")
async def get_person(
    name: str,
) -> tuple[Person, Literal[HTTPStatus.OK]] | tuple[APIError, Literal[HTTPStatus.BAD_REQUEST]]:
    if len(name) < 3:
        return APIError(code=400, message="Name must be at least 3 characters long"), HTTPStatus.BAD_REQUEST
    return Person(id=1, name=name, age=30, employment=Employed(company="Company", position="Position")), HTTPStatus.OK


@routes.post("/person", tags="HR")
async def create_person(
    data: CreatePersonPayload,
) -> tuple[Person, Literal[HTTPStatus.CREATED]] | tuple[APIError, Literal[HTTPStatus.BAD_REQUEST]]:
    if data.age < 0:
        return APIError(code=400, message="Age must be a positive integer"), HTTPStatus.BAD_REQUEST
    return Person(id=1, name=data.name, age=data.age, employment=data.employment), HTTPStatus.CREATED


if __name__ == "__main__":
    app.run(debug=True, port=5001)
