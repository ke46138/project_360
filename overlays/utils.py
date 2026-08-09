from aiogram import Router

def remove_handler(router: Router, handler):
    """Удаляет указанный handler из router.message.handlers"""
    router.message.handlers = [
        h for h in router.message.handlers
        if h.callback != handler
    ]

def remove_handlers_batch(router: Router, callbacks: set):
    """
    Удаляет хендлеры, callback которых содержится в callbacks
    """
    router.message.handlers = [
        h for h in router.message.handlers
        if h.callback not in callbacks
    ]
