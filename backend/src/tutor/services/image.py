"""Image processing service for AI English Tutor.

Provides image validation, base64 encoding, and preprocessing for LLM consumption.
"""

import base64

# Constants for image validation
MAX_IMAGE_SIZE_MB = 10
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ImageValidationError(Exception):
    """Raised when image validation fails."""

    pass


def validate_image(image_data: str, mime_type: str) -> tuple[bool, str]:
    """Validate image size and format.

    Args:
        image_data: Base64 encoded image data
        mime_type: The image MIME type (e.g., "image/jpeg", "image/png")

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if validation passes, False otherwise
        - error_message: Empty string if valid, error description if invalid

    Example:
        >>> is_valid, error = validate_image("base64data...", "image/jpeg")
        >>> if not is_valid:
        ...     print(f"Validation failed: {error}")
    """
    # Check MIME type
    if mime_type not in ALLOWED_MIME_TYPES:
        return (
            False,
            f"Unsupported image format: {mime_type}. Allowed: {ALLOWED_MIME_TYPES}",
        )

    # Check size (base64 encoded size)
    try:
        decoded_size = len(base64.b64decode(image_data, validate=True))
        size_mb = decoded_size / (1024 * 1024)
        if size_mb > MAX_IMAGE_SIZE_MB:
            return (
                False,
                f"Image size ({size_mb:.2f}MB) exceeds limit ({MAX_IMAGE_SIZE_MB}MB)",
            )
    except Exception as e:
        return False, f"Invalid base64 data: {str(e)}"

    return True, ""


def preprocess_image_for_llm(image_data: str, mime_type: str) -> dict:
    """Prepare image for LLM vision API.

    Converts base64 image data to the format expected by LangChain's
    vision API (used by models with vision capabilities like GPT-4o).

    Args:
        image_data: Base64 encoded image data
        mime_type: The image MIME type

    Returns:
        A dict formatted for LangChain vision API consumption

    Example:
        >>> result = preprocess_image_for_llm("base64data...", "image/jpeg")
        >>> # Result: {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
    """
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
    }
