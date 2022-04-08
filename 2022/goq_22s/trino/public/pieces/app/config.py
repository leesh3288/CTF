import datetime
import os

Config = {
    'SECRET_KEY': os.urandom(16),
    'PERMANENT_SESSION_LIFETIME':datetime.timedelta(minutes=5),
    'SESSION_PERMANENT': True,
    'SESSION_USE_SIGNER': True,
    'SESSION_KEY_PREFIX': 's:',
}
