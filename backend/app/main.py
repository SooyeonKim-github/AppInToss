from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.quiz import router as quiz_router
from .api.stats import router as stats_router
from .api.health import router as health_router
from .database.db import init_db

app=FastAPI(title='오를까? 입문편 API', version='0.1.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=False,allow_methods=['*'],allow_headers=['*'])
app.include_router(health_router); app.include_router(quiz_router); app.include_router(stats_router)

@app.on_event('startup')
def startup(): init_db()
