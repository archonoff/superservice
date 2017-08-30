try:
    import ujson as json_lib
except:
    import json as json_lib

from functools import wraps

from aiohttp.web import json_response, Response, HTTPUnauthorized, HTTPForbidden, HTTPInternalServerError

from aiohttp_session import get_session


def login_required(allowed_user_type=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(request):
            session = await get_session(request)
            user_id = session.get('user_id')
            user_type = session.get('user_type')
            if user_id:
                # Пользователь залогинен
                if allowed_user_type is None:
                    return await func(request)
                if allowed_user_type in ('executor', 'customer'):
                    # Проверям статус пользователя
                    if user_type == allowed_user_type:
                        return await func(request)
                    else:
                        raise HTTPForbidden
                else:
                    # В декоратор передан неверный параметр
                    raise HTTPInternalServerError
            else:
                # Пользователь не залогинен
                raise HTTPUnauthorized

        return wrapper
    return decorator


def save_user_to_session(session, user: dict):
    session['user_id'] = user.get('id')
    session['name'] = user.get('name')
    session['login'] = user.get('login')
    session['user_type'] = user.get('type')


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
