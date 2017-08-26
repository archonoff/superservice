import ujson

from aiohttp.web import json_response, Response


def rest_response(code: str, message) -> Response:
    result_dict = {
        'result': code,
        'message': message,
    }
    return json_response(result_dict, dumps=ujson.dumps)


def success_response(message=None):
    return rest_response('success', message)


def error_response(message=None):
    return rest_response('error', message)
