from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from db.db import *

routes = web.RouteTableDef()

@routes.get('/users/{id}/cart')
async def cart(request: Request) -> Response:
    try:
        user_id = int(request.match_info['id'])
        db = request.app[DB_KEY]
        favorite_query = 'SELECT product_id FROM user_cart WHERE user_id = $1'
        result = await db.fetch(favorite_query, user_id)
        if result is not None:
            return web.json_response([dict(record) for record in result])
        raise web.HTTPNotFound()
    except ValueError:
        raise web.HTTPBadRequest()

app = web.Application()
app.on_startup.append(create_db_pool)
app.on_cleanup.append(destroy_db_pool)

app.add_routes(routes)
web.run_app(app, port=8003)