def user_favorites_count(request):
    if request.user.is_authenticated:
        return {'user_favorites_count': request.user.favorites.count()}
    return {'user_favorites_count': 0}
