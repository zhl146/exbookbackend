from rest_core import *

if __name__ == "__main__":
    handler = RotatingFileHandler('/var/log/exbook/exbook.log', maxBytes=100000, backupCount=10)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(handler)
    app.config['PROPAGATE_EXCEPTIONS'] = True

    app.run()
