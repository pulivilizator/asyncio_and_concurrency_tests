import asyncio
from asyncio import Task
import aiohttp
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

import logging
from collections.abc import Awaitable
import functools

from utils.retry import retry


routes = web.RouteTableDef()

PRODUCT_BASE = 'http://localhost:8000'
INVENTORY_BASE = 'http://localhost:8001'
FAVORITE_BASE = 'http://localhost:8002'
CART_BASE = 'http://localhost:8003'


@routes.get('/products/all')
async def all_products(request: Request) -> Response:
    async with aiohttp.ClientSession() as session:
        products, favorites, cart = await create_requests(session)
        requests = [products, favorites, cart]
        done, pending = await asyncio.wait(requests, timeout=1)

        if products in pending:
            [request.cancel() for request in requests]
            return web.json_response(
                {'error': 'Не удалось подключиться к сервису товаров'},
                status=504
            )
        elif products in done and products.exception() is not None:
            [request.cancel() for request in requests]
            logging.exception('Ошибка при подключении к сервису товаров', exc_info=products.exception())
            return web.json_response(
                {'error': 'Не удалось подключиться к сервису товаров'},
                status=500
            )
        else:
            product_response = await products.result().json()
            product_results: list[dict] = await get_product_with_inventory(session, product_response)

            cart_item_count = await get_response_item_count(cart, done, pending, 'ERROR GETTING USER CERT')
            favorite_item_count = await get_response_item_count(favorites, done, pending, 'ERROR GETTING USER FAVORITES')

            return web.json_response(
                {'cart_items': cart_item_count,
                 'favorite_items': favorite_item_count,
                 'products': product_results}
            )


async def get_response_item_count(task: Task, done: set[Awaitable], pending: set[Awaitable], error_msg: str) -> int | None:
    if task in done and task.exception() is None:
        return len(await task.result().json())
    elif task in pending:
        task.cancel()
    else:
        logging.exception(error_msg, exc_info=task.exception())

async def create_requests(session: aiohttp.ClientSession) -> tuple[Task, Task, Task]:
    product_request = functools.partial(session.get, f'{PRODUCT_BASE}/products')
    favorite_request = functools.partial(session.get, f'{FAVORITE_BASE}/users/3/favorites')
    cart_request = functools.partial(session.get, f'{CART_BASE}/users/3/cart')

    products = asyncio.create_task(retry(product_request, 3, .3, .3))
    favorites = asyncio.create_task(retry(favorite_request, 3, .3, .3))
    cart = asyncio.create_task(retry(cart_request, 3, .3, .3))

    return products, favorites, cart

async def get_product_with_inventory(session: aiohttp.ClientSession, product_response) -> list[dict]:

    def get_inventory(session: aiohttp.ClientSession, product_id: str) -> Task:
        url = f'{INVENTORY_BASE}/products/{product_id}/inventory'
        return asyncio.create_task(session.get(url))

    def create_product_record(product_id: int, inventory: int | None) -> dict[[str, int], [str, int | None]]:
        return {'product_id': product_id, 'inventory': inventory}

    inventory_to_product_id = {
        get_inventory(session, product['product_id']): product
        for product in product_response
    }

    product_results = []

    inventory_done, inventory_pending = await asyncio.wait(inventory_to_product_id.keys(), timeout=1)

    for done_task in inventory_done:
        if done_task.exception() is None:
            product_id = inventory_to_product_id[done_task]
            inventory = await done_task.result().json()
            product_results.append(
                create_product_record(product_id, inventory)
            )
        else:
            product_id = inventory_to_product_id[done_task]
            product_results.append(
                create_product_record(product_id, None)
            )
            logging.exception('Не удалось получить сведения о наличии товара', exc_info=done_task.exception())

    for pending_task in inventory_pending:
        pending_task.cancel()
        product_id = inventory_to_product_id[pending_task]
        product_results.append(
            create_product_record(product_id, None)
        )
    return product_results


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=9000)