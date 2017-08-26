try:
    import ujson as json_lib
except:
    import json as json_lib

from aiohttp.web import json_response, Response


def code_response(code: str) -> Response:
    def rest_response(data=None):
        result_dict = {
            'result': code,
            'data': data,
        }
        return json_response(result_dict, dumps=json_lib.dumps)
    return rest_response

success_response = code_response('success')
error_response = code_response('error')
