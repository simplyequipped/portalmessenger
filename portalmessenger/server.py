import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException

from .api import api_routes


def create_app():
    '''Create and configure the Starlette application'''
    # server api routes during development and production
    routes = [
        Mount('/api', routes=api_routes),
    ]
    
    # mount static files and serve spa route if static directory exists (production)
    if os.path.exists('static'):
        routes.extend([
            Mount('/static', StaticFiles(directory='static'), name='static'),
            Route('/', serve_spa),
            Route('/{path:path}', serve_spa),  # SPA fallback routing
        ])
    
    return Starlette(routes=routes, exception_handlers={HTTPException: http_error_handler})

async def serve_spa(request):
    '''Serve the single page application'''
    return FileResponse('static/index.html')

async def http_error_handler(request, exc):
    '''Handle HTTP exceptions'''
    return JSONResponse({'error': str(exc.detail)}, status_code=exc.status_code)

def run_server(host='0.0.0.0', port=8080, **kwargs):
    '''Run the uvicorn server'''
    uvicorn.run(app, host=host, port=port, **kwargs)

app = create_app()
