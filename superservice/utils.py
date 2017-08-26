try:
    import ujson as json_lib
except:
    import json as json_lib

from aiohttp.web import json_response, Response


def rest_response(code: str, message) -> Response:
    result_dict = {
        'result': code,
        'message': message,
    }
    return json_response(result_dict, dumps=json_lib.dumps)


def success_response(message=None):
    return rest_response('success', message)


def error_response(message=None):
    return rest_response('error', message)
