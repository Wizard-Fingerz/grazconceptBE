"""
Shared upload validators for CloudinaryField (and any other FileField/ImageField)
across the project.

Cloudinary fields don't get Django's normal FileExtensionValidator/size checks
for free, so we apply these explicitly wherever user-uploaded documents or
images are accepted.
"""
from django.core.exceptions import ValidationError

# Generic identity/visa-style documents: PDFs and common image formats.
DOCUMENT_EXTENSIONS = ("pdf", "jpg", "jpeg", "png", "doc", "docx")
# Banner/landing-page imagery: images only.
IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "webp", "gif")
# Chat attachments: documents + images, a bit more permissive.
ATTACHMENT_EXTENSIONS = DOCUMENT_EXTENSIONS + ("txt", "csv", "xlsx")

DEFAULT_MAX_UPLOAD_SIZE_MB = 10


def _validate_cloudinary_file(value, allowed_extensions, max_size_mb=DEFAULT_MAX_UPLOAD_SIZE_MB):
    if not value:
        return

    # CloudinaryField gives us a CloudinaryResource; the original filename is
    # available via .name (set from the uploaded file before it's sent off).
    name = getattr(value, "name", None) or str(value)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Unsupported file type '.{ext}'. Allowed types: {', '.join(allowed_extensions)}."
        )

    size = getattr(value, "size", None)
    if size is not None and size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File too large. Maximum allowed size is {max_size_mb}MB.")


def validate_document_file(value):
    _validate_cloudinary_file(value, DOCUMENT_EXTENSIONS)


def validate_image_file(value):
    _validate_cloudinary_file(value, IMAGE_EXTENSIONS)


def validate_attachment_file(value):
    _validate_cloudinary_file(value, ATTACHMENT_EXTENSIONS)
