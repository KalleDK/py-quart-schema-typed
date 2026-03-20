import inspect
from http import HTTPMethod
from types import GenericAlias, UnionType
from typing import Any, Literal, cast, get_args, get_origin

import flask.typing as ft
import quart
import quart_schema

__version__ = "0.1.0"


QUERY_ARGS_KEY = "query_args"
REQUEST_KEY = "data"


# region Method Parsers


def get_query_model(sig: inspect.Signature) -> Any | None:
    if QUERY_ARGS_KEY not in sig.parameters:
        return None
    return sig.parameters[QUERY_ARGS_KEY].annotation


def patch_querystring[T](fn: T, sig: inspect.Signature) -> T:
    query_model = get_query_model(sig)
    if query_model is not None:
        fn = quart_schema.validate_querystring(query_model)(fn)  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
    return cast(T, fn)


def get_request_model(sig: inspect.Signature) -> Any | None:
    if REQUEST_KEY not in sig.parameters:
        return None
    return sig.parameters[REQUEST_KEY].annotation


def patch_request[T](fn: T, sig: inspect.Signature) -> T:
    req_model = get_request_model(sig)
    if req_model is not None:
        fn = quart_schema.validate_request(req_model)(fn)  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
    return cast(T, fn)


def get_response_status(anno: Any) -> Any:
    origin = get_origin(anno)
    if origin is Literal:
        return get_args(anno)[0]
    return anno


def get_response_model(anno: GenericAlias) -> tuple[Any, Any]:
    model, status = get_args(anno)
    return model, get_response_status(status)


def get_response_models(sig: inspect.Signature) -> list[tuple[Any, Any]]:
    resp = sig.return_annotation

    origin = get_origin(resp)
    if origin is tuple:
        return [get_response_model(resp)]

    if origin is UnionType:
        return [get_response_model(part) for part in get_args(resp)]

    raise Exception(f"can't parse signature {origin} {type(origin)}")


def patch_response[T](fn: T, sig: inspect.Signature) -> T:
    responses = get_response_models(sig)
    for response in responses:
        model, status = response
        fn = quart_schema.validate_response(model, status)(fn)  # pyright: ignore[reportAssignmentType, reportReturnType, reportArgumentType, reportUnknownVariableType, reportUnknownMemberType]
    return cast(T, fn)


def patch_tags[T](fn: T, tags: None | str | list[str]) -> T:
    if tags is not None:
        if isinstance(tags, str):
            tags = [tags]
        fn = cast(T, quart_schema.tag(tags)(fn))  # ty: ignore[invalid-argument-type] # pyright: ignore[reportArgumentType]
    return fn


class RouteReg:
    app: quart.Quart
    method: HTTPMethod
    url: str
    tags: list[str]

    __slots__ = ("app", "method", "url", "tags")

    def __init__(self, app: quart.Quart, method: HTTPMethod, url: str, tags: None | str | list[str] = None) -> None:
        self.app = app
        self.method = method
        self.url = url
        match tags:
            case None:
                self.tags = [self.url.split("/")[1].title()] if len(self.url.split("/")) > 1 else ["default"]
            case str():
                self.tags = [tags]
            case list():
                self.tags = tags
            case _:
                raise ValueError(f"Invalid tags: {tags}")

    def __call__[T: ft.RouteCallable](self, fn: T) -> T:
        sig = inspect.signature(fn)

        fn = patch_tags(fn, self.tags)
        if self.method in [HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH]:
            fn = patch_request(fn, sig)
        fn = patch_querystring(fn, sig)
        fn = patch_response(fn, sig)

        match self.method:
            case HTTPMethod.GET:
                self.app.get(self.url)(fn)
            case HTTPMethod.POST:
                self.app.post(self.url)(fn)
            case HTTPMethod.PUT:
                self.app.put(self.url)(fn)
            case HTTPMethod.DELETE:
                self.app.delete(self.url)(fn)
            case HTTPMethod.PATCH:
                self.app.patch(self.url)(fn)
            case _:
                raise ValueError(f"Unsupported HTTP method: {self.method}")
        return fn


class RouteMgr:
    app: quart.Quart

    __slots__ = ("app",)

    def __init__(self) -> None:
        self.app = quart.Quart(__name__)

    def get(self, url: str, tags: None | str | list[str] = None) -> RouteReg:
        return RouteReg(app=self.app, method=HTTPMethod.GET, url=url, tags=tags)

    def post(self, url: str, tags: None | str | list[str] = None) -> RouteReg:
        return RouteReg(app=self.app, method=HTTPMethod.POST, url=url, tags=tags)

    def put(self, url: str, tags: None | str | list[str] = None) -> RouteReg:
        return RouteReg(app=self.app, method=HTTPMethod.PUT, url=url, tags=tags)

    def delete(self, url: str, tags: None | str | list[str] = None) -> RouteReg:
        return RouteReg(app=self.app, method=HTTPMethod.DELETE, url=url, tags=tags)

    def patch(self, url: str, tags: None | str | list[str] = None) -> RouteReg:
        return RouteReg(app=self.app, method=HTTPMethod.PATCH, url=url, tags=tags)


# endregion

__all__ = ["RouteMgr"]
