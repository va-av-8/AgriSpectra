import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import init_db
from routes.home import home_route
from routes.admin import admin_route
from routes.user import user_route
from routes.service import service_route


app = FastAPI()
app.include_router(home_route)
app.include_router(admin_route)
app.include_router(user_route)
app.include_router(service_route)


origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


if __name__ == "__main__":
    uvicorn.run("api:app", host='0.0.0.0', port=8080, reload=True)
