"""Root URL configuration. Every app's routes are mounted under /api/v1/."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1 = [
    path("common/", include("apps.common.api.urls")),
    path("accounts/", include("apps.accounts.api.urls")),
    path("social/", include("apps.social.api.urls")),
    path("puzzles/", include("apps.puzzles.api.urls")),
    path("results/", include("apps.results.api.urls")),
    path("games/word/", include("apps.games.word.api.urls")),
    path("games/logic/", include("apps.games.logic.api.urls")),
    path("games/math/", include("apps.games.math.api.urls")),
    path("games/trivia/", include("apps.games.trivia.api.urls")),
    path("games/geo/", include("apps.games.geo.api.urls")),
    path("leaderboards/", include("apps.leaderboards.api.urls")),
    path("stats/", include("apps.stats.api.urls")),
    path("subscriptions/", include("apps.subscriptions.api.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
