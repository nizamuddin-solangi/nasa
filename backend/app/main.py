import logging, os
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from .schemas import Query, CompareQuery, ReportRequest
from .nasa import VARIABLES, fetch, NasaError
from .analysis import analyze, compare
from . import store
from .reports import pdf
logging.basicConfig(level=logging.INFO)
app=FastAPI(title='EARTHSCOPE API')
origins=[item.strip() for item in os.getenv('EARTHSCOPE_CORS_ORIGINS','http://localhost:5173').split(',') if item.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST'],allow_headers=['Content-Type'])
@app.on_event('startup')
def setup(): store.init()
@app.get('/api/health')
def health(): return {'status':'ok'}
@app.get('/api/nasa/variables')
def variables(): return VARIABLES
@app.get('/api/nasa/data')
async def data(q: Query = Depends()):
 try:return await fetch(q)
 except NasaError as e: raise HTTPException(503,str(e))
@app.post('/api/analysis/trend')
async def trend(q: Query):
 try: return analyze(**(await fetch(q)))
 except NasaError as e: raise HTTPException(503,str(e))
 except ValueError as e: raise HTTPException(422,str(e))
@app.post('/api/investigations')
async def investigation(q: Query):
 try: result=analyze(**(await fetch(q))); ident=store.save(result); return {'id':ident,'result':result}
 except NasaError as e: raise HTTPException(503,str(e))
@app.get('/api/investigations/{ident}')
def get_investigation(ident:str):
 result=store.get(ident)
 if not result: raise HTTPException(404,'Investigation not found')
 return result
@app.get('/api/investigations')
def recent_investigations(limit:int=20):
 if limit < 1 or limit > 100: raise HTTPException(422,'limit must be between 1 and 100')
 return store.list_recent(limit)
@app.post('/api/analysis/compare')
async def compare_locations(q:CompareQuery):
 try:
  a=analyze(**(await fetch(q.first))); b=analyze(**(await fetch(q.second))); return compare(a,b)
 except NasaError as e: raise HTTPException(503,str(e))
@app.post('/api/reports/generate')
def report(q:ReportRequest): return Response(pdf(q.title,q.result),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename=earthscope-report.pdf'})
static_dir=os.getenv('EARTHSCOPE_STATIC_DIR')
if static_dir and os.path.isdir(static_dir): app.mount('/', StaticFiles(directory=static_dir, html=True), name='frontend')
