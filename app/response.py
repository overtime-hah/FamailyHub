"""统一 API 响应格式"""
from flask import jsonify


def success(data=None, msg="ok", code=200):
    """统一成功响应格式"""
    body = {"code": 0, "msg": msg}
    if data is not None:
        body["data"] = data
    return jsonify(body), code


def error(msg="请求失败", code=400, error_code=None):
    """统一错误响应格式"""
    body = {"code": error_code or code, "msg": msg}
    return jsonify(body), code


def created(data=None, msg="创建成功"):
    """201 响应"""
    return success(data=data, msg=msg, code=201)


def not_found(msg="资源不存在"):
    """404 响应"""
    return error(msg=msg, code=404)


def forbidden(msg="无权操作"):
    """403 响应"""
    return error(msg=msg, code=403)


def unauthorized(msg="未授权"):
    """401 响应"""
    return error(msg=msg, code=401)


def server_error(msg="服务器内部错误"):
    """500 响应"""
    return error(msg=msg, code=500)
