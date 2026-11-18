# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""EcoTracker Enterprise Security and Guardrails Engine.

Provides multi-layer security filtering including:
- PII scrubbing (emails, international phone numbers, addresses, financial IDs)
- Context-aware credential filtering (avoiding false positives on technical units)
- Prompt injection & jailbreak detection
- Structured JSON audit logging
"""

import re
import json
import datetime
from typing import NamedTuple

class SecurityCheckResult(NamedTuple):
    passed: bool
    sanitized_text: str
    rejection_reason: str | None = None
    pii_redacted: bool = False
    audit_event: dict | None = None

def write_audit_log(severity: str, action: str, details: dict) -> None:
    """Emits structured JSON audit log to stdout."""
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": action,
        "severity": severity,
        "details": details
    }
    print(f"[AUDIT_LOG] {json.dumps(log_entry)}")

# Comprehensive prompt injection, jailbreak, and system override signatures
INJECTION_PATTERNS = [
    # System prompt / instructions leakage
    r"ignore\s+(all\s+)?(previous|prior|above|existing)\s+(instructions|directives|rules|constraints|prompt)",
    r"disregard\s+(all\s+)?(previous|prior|above|existing)\s+(instructions|directives|rules|constraints|prompt)",
    r"forget\s+(all\s+)?(previous|prior|above|existing|your)\s+(instructions|directives|rules|constraints|prompt)",
    r"(reveal|show|print|display|dump|tell\s+me)\s+(the\s+|your\s+|secret\s+)?(system\s+prompt|developer\s+mode|internal\s+instructions|initial\s+prompt)",
    r"what\s+(is|was)\s+(your|the)\s+(system\s+prompt|initial\s+instructions?|hidden\s+prompt)",
    r"repeat\s+the\s+words?\s+above",
    r"repeat\s+(everything|all\s+text)\s+(above|from\s+line\s+1)",
    
    # Persona jailbreaks & modes
    r"you\s+are\s+now\s+(in\s+)?(dan|jailbreak|unrestricted|god\s*mode|developer\s*mode|evil\s*mode)",
    r"act\s+as\s+an?\s+(unrestricted|unfiltered|jailbroken|evil|dan|developer\s*mode)\s+(ai|model|assistant|bot)",
    r"pretend\s+(you\s+have|you\s+are|there\s+are)\s+no\s+(rules|limits|safety|filters|guardrails|guidelines)",
    r"do\s+anything\s+now\b",
    
    # Security bypass
    r"(bypass|override|disable)\s+(all\s+)?(security|guardrails|safety\s+filters?|rules|restrictions)",
    r"\bsystem\s+override\b",
    r"\b(sudo\s+mode|root\s+access|god\s+mode\s+activated)\b",
    r"new\s+(system\s+)?instructions?:",

    # Script & code execution / XSS injection
    r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
    r"javascript:\s*",
    r"onerror\s*=|onload\s*=",
    r"\b(eval|exec)\s*\(",
    r"\b(os\.system|subprocess\.(Popen|run|call)|import\s+os)\b",

    # SQL Injection attempts
    r"\b(UNION\s+ALL\s+SELECT|UNION\s+SELECT|DROP\s+TABLE|DELETE\s+FROM\s+\w+|UPDATE\s+\w+\s+SET)\b",
    r"'\s*OR\s*['\"0-9a-zA-Z]+\s*=\s*['\"0-9a-zA-Z]+(\s*--|\s*#|\s*/\*)",
]

# Sensitive credentials - context-aware to prevent false positives like "3-pin plug" or "push pin"
CREDENTIAL_PATTERNS = [
    r"\b(password|passwd|pwd)\s*[:=]\s*\S+",
    r"\bmy\s+password\s+is\s+\S+",
    r"\b(api[_-]?key|secret[_-]?key|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]?\s*\S{8,}\b",
    r"\bBearer\s+[A-Za-z0-9_\-\.]{15,}\b",
    r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b",
    r"\bAIzaSy[A-Za-z0-9_\-]{33}\b",
    r"\bgsk_[A-Za-z0-9]{20,}\b",
    r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----",
    r"\b(pin\s*(code|number)?|passcode)\s*[:=]?\s*\d{4,8}\b",
    r"\b(atm\s*pin|account\s*pin)\b",
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN (Social Security Number)
]


# Regex patterns for PII detection
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

# International and domestic phone numbers: e.g., +1-555-123-4567, (555) 123-4567, +91 98765 43210
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)

# Address pattern: checks for building numbers followed by street designations,
# with strict negative lookahead to prevent false positives on distance/energy units
ADDRESS_REGEX = re.compile(
    r"\b\d+\s+(?!(?:km|kms|kilometer|kilometers|mile|miles|mi|meter|meters|m|yards|yd|kg|lbs|kwh|watt|watts|kph|mph)\b)"
    r"[A-Za-z0-9\s]{2,30}\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Court|Ct|Way|Terrace|Place|Pl)\b",
    re.IGNORECASE
)

# Credit card numbers (13-16 digits formatted or continuous)
CREDIT_CARD_REGEX = re.compile(
    r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{15,16}\b"
)

def inspect_and_sanitize(
    user_text: str,
    injection_enabled: bool = True,
    pii_enabled: bool = True,
    credential_filter_enabled: bool = True
) -> SecurityCheckResult:
    """Inspects text for security threats, scrubs PII, and returns sanitization status."""
    
    # 1. Prompt Injection & Jailbreak Check
    if injection_enabled:
        for pattern in INJECTION_PATTERNS:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                audit = {
                    "matched_pattern": pattern,
                    "matched_snippet": match.group(0),
                    "status": "blocked"
                }
                write_audit_log(severity="CRITICAL", action="prompt_injection_check", details=audit)
                return SecurityCheckResult(
                    passed=False,
                    sanitized_text=user_text,
                    rejection_reason="Security Check Failed: Request blocked due to potential prompt injection.",
                    audit_event=audit
                )

    # 2. Context-Aware Credential Check
    if credential_filter_enabled:
        for pattern in CREDENTIAL_PATTERNS:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                audit = {
                    "matched_pattern": pattern,
                    "matched_snippet": match.group(0),
                    "status": "blocked"
                }
                write_audit_log(severity="WARNING", action="credential_filter_check", details=audit)
                return SecurityCheckResult(
                    passed=False,
                    sanitized_text=user_text,
                    rejection_reason="Security Check Failed: Request contains sensitive passwords or credential secrets.",
                    audit_event=audit
                )

    # 3. PII Scrubbing
    scrubbed_text = user_text
    pii_found = False

    if pii_enabled:
        if EMAIL_REGEX.search(scrubbed_text):
            scrubbed_text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", scrubbed_text)
            pii_found = True

        if PHONE_REGEX.search(scrubbed_text):
            scrubbed_text = PHONE_REGEX.sub("[REDACTED_PHONE]", scrubbed_text)
            pii_found = True

        if ADDRESS_REGEX.search(scrubbed_text):
            scrubbed_text = ADDRESS_REGEX.sub("[REDACTED_ADDRESS]", scrubbed_text)
            pii_found = True

        if CREDIT_CARD_REGEX.search(scrubbed_text):
            scrubbed_text = CREDIT_CARD_REGEX.sub("[REDACTED_FINANCIAL_ID]", scrubbed_text)
            pii_found = True

    audit = {
        "pii_scrubbed": pii_found,
        "status": "passed"
    }
    write_audit_log(severity="INFO", action="security_checkpoint_passed", details=audit)

    return SecurityCheckResult(
        passed=True,
        sanitized_text=scrubbed_text,
        pii_redacted=pii_found,
        audit_event=audit
    )
