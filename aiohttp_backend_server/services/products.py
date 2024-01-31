from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from db.db import *

routes = web.RouteTableDef()

@routes.get('/products')
async def products(request: Request) -> Response:
    db = request.app[DB_KEY]
    product_query = 'SELECT product_id, product_name FROM product'
    result = await db.fetch(product_query)
    return web.json_response([dict(record) for record in result])


app = web.Application()
app.on_startup.append(create_db_pool)
app.on_cleanup.append(destroy_db_pool)

app.add_routes(routes)
web.run_app(app, port=8000)