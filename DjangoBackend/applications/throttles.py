from rest_framework.throttling import UserRateThrottle


class MatchThrottle(UserRateThrottle):
    scope = "match"     # rate comes from settings