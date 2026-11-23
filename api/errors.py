"""Stable error codes for errors returned by the application API."""

from __future__ import annotations

from enum import IntEnum


class ApiErrorCode(IntEnum):
    INVALID_REQUEST = 4001
    RESOURCE_NOT_FOUND = 4002
    IMPORT_ALREADY_RUNNING = 4003
    UNKNOWN_API_ERROR = 4004
    INTERNAL_ERROR = 5001


def error_code_for_status(status_code: int) -> ApiErrorCode:
    if status_code == 404:
        return ApiErrorCode.RESOURCE_NOT_FOUND
    if status_code == 409:
        return ApiErrorCode.IMPORT_ALREADY_RUNNING
    if status_code == 422:
        return ApiErrorCode.INVALID_REQUEST
    if status_code >= 500:
        return ApiErrorCode.INTERNAL_ERROR
    if 400 <= status_code < 500:
        return ApiErrorCode.UNKNOWN_API_ERROR
    return ApiErrorCode.INTERNAL_ERROR
