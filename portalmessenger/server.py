import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from .api import api_routes


def create_app():
    '''Create and configure the Starlette application'''
    # cors middleware
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
    ]
    
    # mount static files and serve spa route if static directory exists (production)  
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if os.path.exists(static_dir):
        routes = [
            Mount('/api', routes=api_routes),
            Mount('/_app', StaticFiles(directory=os.path.join(static_dir, '_app')), name='app'),
            Route('/', serve_spa),
            Route('/{path:path}', serve_spa),  # SPA fallback routing
        ]
    else:
        # development mode - only API routes
        routes = [
            Mount('/api', routes=api_routes),
        ]
    
    return Starlette(
        routes=routes, 
        middleware=middleware,
        exception_handlers={HTTPException: http_error_handler}
    )

async def serve_spa(request):
    '''Serve the single page application'''
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return FileResponse(os.path.join(static_dir, 'index.html'))

async def http_error_handler(request, exc):
    '''Handle HTTP exceptions'''
    return JSONResponse({'error': str(exc.detail)}, status_code=exc.status_code)

def run_server(host='0.0.0.0', port=8080, debug=False, **kwargs):
    '''Run the uvicorn server'''
    log_level = 'debug' if debug else 'error'
    uvicorn.run(app, host=host, port=port, log_level=log_level, **kwargs)

app = create_app()
