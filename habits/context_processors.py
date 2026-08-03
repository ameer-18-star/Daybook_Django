"""
Makes the current user's UserSettings available in every template as
`global_user_settings`, without every single view needing to fetch and
pass it — used by base.html to set the accent-color/card-theme
attributes on <html>, and by nav headers to show the avatar.

Named distinctly from the `user_settings` key several views already pass
in their own context (Profile, Timeline, Habits list) so there's no
collision — those view-level values still take precedence in their own
templates; this is only a fallback for everywhere else.
"""
from .models import UserSettings


def user_preferences(request):
    if getattr(request, 'user', None) and request.user.is_authenticated:
        return {'global_user_settings': UserSettings.get_for(request.user)}
    return {'global_user_settings': None}