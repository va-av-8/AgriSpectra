from fastapi import APIRouter


home_route = APIRouter(tags=['Home'])


# This will be the start page after web UI developing
@home_route.get('/')
async def index():
    return {"message": "Hello home route"}
