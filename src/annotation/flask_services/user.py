
#For user authentication
class ForwardedUserMiddleware(object):
    def __init__(self, application):
        self.app = application

    def __call__(self, environ, start_response):
        user = environ.pop('HTTP_X_FORWARDED_USER', None)
        if user is not None:
            environ['REMOTE_USER'] = user.split("@")[0]

        return self.app(environ, start_response)