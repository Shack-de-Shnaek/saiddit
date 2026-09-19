"""Global API exception handlers.

These supersede the defaults django-ninja installs, so every error the API
emits shares one envelope:

    {"detail": "...", "errors": {"<field>": ["..."], "__all__": ["..."]}}

`errors` is only present when something field-specific is known. Errors that
belong to the request as a whole rather than to one field are collected under
`__all__` (Django's NON_FIELD_ERRORS).
"""
from django.conf import settings
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    ObjectDoesNotExist,
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from django.db import IntegrityError
from django.http import Http404
from ninja.errors import (
    AuthenticationError,
    HttpError,
    ValidationError as RequestValidationError,
)

# Parameter sources django-ninja puts at the head of a pydantic error `loc`.
_BODY_SOURCES = ('body', 'form', 'file')


def error_response(detail, errors=None):
    payload = {'detail': detail}

    if errors:
        payload['errors'] = errors

    return payload


def django_validation_errors(exc):
    """Split a Django ValidationError into per-field and non-field messages."""
    if hasattr(exc, 'error_dict'):
        return {field: list(messages) for field, messages in exc.message_dict.items()}

    return {NON_FIELD_ERRORS: list(exc.messages)}


def request_validation_errors(errors):
    """Group pydantic request errors by the field they came from.

    A `loc` of ('body', 'payload', 'name') is the body field `name`, while
    ('body', 'payload') is about the body as a whole and lands in `__all__`.
    """
    grouped = {}

    for error in errors:
        location = [str(part) for part in error.get('loc', ())]
        source, path = (location[0], location[1:]) if location else ('', [])

        if source in _BODY_SOURCES:
            # Drop the view's parameter name; callers never see it.
            path = path[1:]

        field = '.'.join(path) if path else NON_FIELD_ERRORS
        grouped.setdefault(field, []).append(error.get('msg', 'Invalid value.'))

    return grouped


def register_error_handlers(api):
    """Attach the handlers to a NinjaAPI instance."""

    @api.exception_handler(RequestValidationError)
    def on_request_validation_error(request, exc):
        return api.create_response(
            request,
            error_response('The request could not be validated.', request_validation_errors(exc.errors)),
            status=422,
        )

    @api.exception_handler(DjangoValidationError)
    def on_model_validation_error(request, exc):
        return api.create_response(
            request,
            error_response('Validation failed.', django_validation_errors(exc)),
            status=400,
        )

    @api.exception_handler(IntegrityError)
    def on_integrity_error(request, exc):
        return api.create_response(
            request,
            error_response('That change conflicts with existing data.'),
            status=409,
        )

    @api.exception_handler(AuthenticationError)
    def on_authentication_error(request, exc):
        return api.create_response(
            request,
            error_response('Authentication is required.'),
            status=401,
        )

    @api.exception_handler(DjangoPermissionDenied)
    def on_permission_denied(request, exc):
        return api.create_response(
            request,
            error_response(str(exc) or 'You do not have permission to do that.'),
            status=403,
        )

    @api.exception_handler(Http404)
    def on_not_found(request, exc):
        return api.create_response(
            request,
            error_response(str(exc) or 'Not found.'),
            status=404,
        )

    @api.exception_handler(ObjectDoesNotExist)
    def on_does_not_exist(request, exc):
        return api.create_response(request, error_response('Not found.'), status=404)

    @api.exception_handler(HttpError)
    def on_http_error(request, exc):
        return api.create_response(
            request,
            error_response(str(exc)),
            status=exc.status_code,
        )

    @api.exception_handler(Exception)
    def on_unhandled_error(request, exc):
        # Let the debug page surface the traceback while developing.
        if settings.DEBUG:
            raise exc

        return api.create_response(
            request,
            error_response('Something went wrong.'),
            status=500,
        )

    return api
