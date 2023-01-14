# Self-made exceptions

class TokenError(Exception):
    """Surely TokenError speaks for itself?"""
    pass


class ChatIdError(Exception):
    """I mean, it's obvious, innit?"""
    pass


class ResponseError(Exception):
    """API didn't return 200"""
    pass


class HomeworkError(Exception):
    """Homework didn't return what was expected"""
    pass
