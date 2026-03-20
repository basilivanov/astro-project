import os


def _flag_enabled(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def is_one_off_entitlements_runtime_enabled() -> bool:
    return _flag_enabled("ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME", default=False)


def use_persistent_checkout_sessions() -> bool:
    return _flag_enabled("ENABLE_PERSISTENT_CHECKOUT_SESSIONS", default=False)


def allow_legacy_premium_subscription_access() -> bool:
    return _flag_enabled("LEGACY_PREMIUM_SUBSCRIPTION_ACCESS", default=True)


def get_feature_flag_snapshot() -> dict[str, bool]:
    return {
        "enable_one_off_entitlements_runtime": is_one_off_entitlements_runtime_enabled(),
        "enable_persistent_checkout_sessions": use_persistent_checkout_sessions(),
        "legacy_premium_subscription_access": allow_legacy_premium_subscription_access(),
    }
