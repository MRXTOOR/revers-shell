"""Main application entry point."""
from flask import Flask
from flask_cors import CORS
from app.routes import api
from app.config import Config


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['DEBUG'] = Config.DEBUG
    
    # Enable CORS for all routes
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    @app.route('/', methods=['GET'])
    def index():
        """Root endpoint."""
        return {
            'name': 'Reverse Shell Backend',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'register': '/api/register',
                'poll': '/api/poll/<session_id>',
                'result': '/api/result/<session_id>',
                'sessions': '/api/sessions',
                'session_detail': '/api/sessions/<session_id>',
                'send_command': '/api/sessions/<session_id>/command'
            }
        }
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)

