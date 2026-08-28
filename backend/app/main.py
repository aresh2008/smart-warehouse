from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base,engine
from .routers.core import r
Base.metadata.create_all(engine)
app=FastAPI(title='SMART WAREHOUSE MANAGEMENT SYSTEM')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(r)
@app.get('/')
def root(): return {'name':'SMART WAREHOUSE MANAGEMENT SYSTEM','docs':'/docs'}
