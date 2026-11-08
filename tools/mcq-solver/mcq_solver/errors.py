"""Only allowlisted error codes cross the diagnostic boundary."""

PAUSE_CODES = {
    "subscription_sharing_usage_limit_exceeded", "subscription_sharing_usage_unavailable",
    "subscription_sharing_user_not_eligible", "subscription_sharing_invalid_user",
    "subscription_sharing_route_not_supported", "subscription_sharing_unsupported_capability",
    "chatpass_v2_scope_not_authorized", "chatpass_v2_invalid_authorization_context",
    "invalid_grant", "invalid_client", "invalid_refresh_token", "token_expired",
    "refresh_token_expired", "refresh_token_invalidated", "refresh_token_reused",
    "auth_required", "permission_denied", "model_unavailable", "reasoning_unsupported",
    "missing_plan_scope", "eligibility_unconfirmed", "plan_approval_required",
    "credits_not_confirmed_disabled", "session_transferred", "preflight_required",
    "invalid_identity", "invalid_credentials",
}
TRANSIENT_CODES = {"network_error", "server_error", "rate_limited", "stream_truncated",
                   "subscription_sharing_user_unavailable"}
LOCAL_CODES = {
    "invalid_config", "api_key_disabled", "invalid_response", "response_failed",
    "response_incomplete", "stream_too_large", "invalid_option", "invalid_explanation",
    "invalid_question_id", "invalid_json", "invalid_question", "stale_source",
    "lost_lease", "worker_busy", "invalid_callback", "access_denied", "invalid_identity",
    "invalid_credentials", "unsafe_permissions", "unsafe_path", "invalid_catalog",
    "http_error", "limit_exceeds_phase", "queue_paused", "transfer_uncertain",
    "host_not_initialized", "duplicate_id", "invalid_packet", "internal_error",
    "stopped", "max_attempts", "invalid_request", "invalid_probe", "missing_bank",
}


class SolverError(Exception):
    def __init__(self, code: str, *, status: int | None = None, retry_after: float = 0):
        self.code = code if code in PAUSE_CODES | TRANSIENT_CODES | LOCAL_CODES else "http_error"
        self.status = status
        self.retry_after = max(0, min(retry_after, 86400))
        super().__init__(self.code)

    @property
    def pauses(self) -> bool:
        return self.code in PAUSE_CODES

    @property
    def transient(self) -> bool:
        return self.code in TRANSIENT_CODES
