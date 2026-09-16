from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat


class MaxFileSizeValidator:
    """Rejects an uploaded file larger than `max_size_kb` kilobytes. A real
    class (not a lambda/closure) so Django's migration serializer can
    import it by reference — same requirement as any validator attached to
    a model field."""

    def __init__(self, max_size_kb):
        self.max_size_kb = max_size_kb

    def __call__(self, file):
        max_bytes = self.max_size_kb * 1024
        if file.size > max_bytes:
            raise ValidationError(
                f'File too large ({filesizeformat(file.size)}). Maximum allowed size is {filesizeformat(max_bytes)}.'
            )

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_size_kb == other.max_size_kb

    def deconstruct(self):
        # Tells Django's migration writer how to reconstruct this validator
        # from source (path, args, kwargs) — required for any custom
        # validator instance used on a model field, same contract as a
        # custom field class.
        return ('core.validators.MaxFileSizeValidator', [self.max_size_kb], {})
