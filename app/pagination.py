"""分页辅助函数"""
from flask import request


def get_pagination_params(default_per_page=20, max_per_page=100):
    """从请求参数中获取分页参数"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", default_per_page, type=int)
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)
    return page, per_page


def paginate_query(query, page, per_page):
    """对查询进行分页，返回分页结果字典"""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": pagination.items,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }
