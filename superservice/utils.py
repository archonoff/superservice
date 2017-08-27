try:
    import ujson as json_lib
except:
    import json as json_lib

from functools import wraps

from aiohttp.web import json_response, Response, HTTPUnauthorized

from aiohttp_session import get_session


def login_required(func):
    @wraps(func)
    async def wrapper(request):
        session = await get_session(request)
        user_id = session.get('user_id')
        if user_id:
            # Пользователь залогинен
            return await func(request)
        else:
            # Пользователь не залогинен
            raise HTTPUnauthorized

    return wrapper


def save_user_to_session(session, user: dict):
    session['user_id'] = user.get('id')
    session['name'] = user.get('name')
    session['login'] = user.get('login')
    session['user_type'] = user.get('user_type')


def code_response(status: str, code: int):
    def rest_response(data=None) -> Response:
        result_dict = {
            'result': status,
            'data': data,
        }
        return json_response(result_dict, status=code, dumps=json_lib.dumps)
    return rest_response

success_response = code_response('success', 200)
error_response = code_response('error', 400)
