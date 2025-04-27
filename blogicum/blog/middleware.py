from django.middleware.csrf import get_token


class LogoutMiddleware:
    """
    Middleware для обработки GET-запросов к логауту.
    Преобразует GET в POST для стандартного LogoutView Django.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем, является ли запрос GET-запросом к логауту
        if (request.path == '/auth/logout/'
                and request.method == 'GET'
                and request.user.is_authenticated):

            # Создаем POST-запрос
            request.method = 'POST'

            # Получаем CSRF-токен
            csrf_token = get_token(request)

            # Создаем POST-данные с CSRF-токеном
            request.POST = request.POST.copy()
            request.POST['csrfmiddlewaretoken'] = csrf_token

        return self.get_response(request)
