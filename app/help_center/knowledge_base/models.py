from django.db import models

from definition.models import TableDropDownDefinition


class FaqArticle(models.Model):
    """
    A frequently asked question and answer entry for the knowledge base.
    """
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        limit_choices_to={'table_name': 'faq_category'},
        related_name="faqs",
        null=True,
        blank=True,
        help_text="The category of this FAQ. Defaults to 'Others' if not set."
    )
    is_active = models.BooleanField(default=True, help_text="If unchecked, this FAQ will not be shown.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "FAQ Article"
        verbose_name_plural = "FAQ Articles"
        ordering = ["category__term", "question"]

    def __str__(self):
        return self.question
