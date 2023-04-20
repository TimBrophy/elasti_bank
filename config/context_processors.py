def add_username(request):
    context = {}
    if request.user.is_authenticated:
        context['username'] = request.user.username
    return context
