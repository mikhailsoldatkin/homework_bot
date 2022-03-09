class BotKeyError(KeyError):
    """Ошибка возникает в случае отсутствия ключа словаря. В аргументах
    указывается проверяемый словарь и имя ключа.
    """

    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return 'в словаре {} нет ключа "{}"!'.format(*self.args)


class BotTypeError(TypeError):
    """Ошибка возникает в случае несоответствия типов данных. В аргументах
    указывается проверяемый объект и ожидаемый тип данных.
    """

    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return "тип данных {} не '{}'!".format(*self.args)


class ResponseError(Exception):
    pass


class SendMessageError(Exception):
    pass
