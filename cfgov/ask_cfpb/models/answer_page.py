from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models
from django.utils.html import strip_tags
from django.utils.text import Truncator

from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.fields import RichTextField, StreamField

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtailautocomplete.edit_handlers import AutocompletePanel

from ask_cfpb.models import blocks as ask_blocks
from v1 import blocks as v1_blocks
from v1.atomic_elements import molecules, organisms
from v1.models import CFGOVPage, PortalCategory, PortalTopic
from v1.models.snippets import RelatedResource, ReusableText


REUSABLE_TEXT_TITLES = {
    "about_us": {
        "en": "About us (For consumers)",
        "es": "About us (for consumers) (in Spanish)",
    },
    "disclaimer": {
        "en": "Legal disclaimer for consumer materials",
        "es": "Legal disclaimer for consumer materials (in Spanish)",
    },
}


def truncate_by_words_and_chars(text, word_limit=40, char_limit=255):
    """Truncate text by whole words until it gets under the character limit.

    Tries truncating by words to word_limit. If the result is not under the
    char_limit, reduce the word_limit by 1 and try again. When it's under the
    char_limit, return it.
    """

    while word_limit:
        truncated = Truncator(text).words(word_limit, truncate=" ...")

        if len(truncated) <= char_limit:
            return truncated

        word_limit -= 1


def get_ask_breadcrumbs(language="en", portal_topic=None):
    DEFAULT_CRUMBS = {
        "es": [
            {
                "title": "Obtener respuestas",
                "href": "/es/obtener-respuestas/",
            }
        ],
        "en": [
            {
                "title": "Ask CFPB",
                "href": "/ask-cfpb/",
            }
        ],
    }
    if portal_topic:
        page = get_portal_or_portal_search_page(
            portal_topic=portal_topic, language=language
        )
        crumbs = [{"title": page.title, "href": page.url}]
        return crumbs
    return DEFAULT_CRUMBS[language]


def get_portal_or_portal_search_page(portal_topic, language="en"):
    if portal_topic:
        portal_page = portal_topic.portal_pages.filter(
            language=language, live=True
        ).first()
        if portal_page:
            return portal_page
        else:
            portal_search_page = portal_topic.portal_search_pages.filter(
                language=language, live=True
            ).first()
            return portal_search_page
    return None


def get_reusable_text_snippet(snippet_title):
    try:
        return ReusableText.objects.get(title=snippet_title)
    except ReusableText.DoesNotExist:
        pass


def get_standard_text(language, text_type):
    return get_reusable_text_snippet(REUSABLE_TEXT_TITLES[text_type][language])


class AnswerPage(CFGOVPage):
    """Page type for Ask CFPB answers."""

    from ask_cfpb.models.django import Answer

    last_edited = models.DateField(
        blank=True,
        null=True,
        help_text="Change the date to today if you make a significant change.",
    )
    question = models.TextField(blank=True)
    statement = models.TextField(
        blank=True,
        help_text=(
            "(Optional) Use this field to rephrase the question title as "
            "a statement. Use only if this answer has been chosen to appear "
            "on a money topic portal (e.g. /consumer-tools/debt-collection)."
        ),
    )
    short_answer = RichTextField(
        blank=True,
        features=["link", "document-link"],
        help_text="Optional answer intro",
    )
    answer_content = StreamField(
        ask_blocks.AskAnswerContent(),
        blank=True,
        verbose_name="Answer",
        use_json_field=True,
    )
    answer_base = models.ForeignKey(
        Answer,
        blank=True,
        null=True,
        related_name="answer_pages",
        on_delete=models.SET_NULL,
    )
    featured = models.BooleanField(
        default=False,
        help_text=(
            "Check to make this one of two featured answers "
            "on the landing page."
        ),
    )
    featured_rank = models.IntegerField(blank=True, null=True)
    category = models.ManyToManyField(
        "Category",
        blank=True,
        help_text=(
            "Categorize this answer. "
            "Avoid putting into more than one category."
        ),
    )
    search_tags = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Search words or phrases, separated by commas",
    )
    related_resource = models.ForeignKey(
        RelatedResource, blank=True, null=True, on_delete=models.SET_NULL
    )
    related_questions = ParentalManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="related_question",
        help_text="Maximum of 3 related questions",
    )
    portal_topic = ParentalManyToManyField(
        PortalTopic,
        blank=True,
        help_text="Limit to 1 portal topic if possible",
    )
    primary_portal_topic = ParentalKey(
        PortalTopic,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="primary_portal_topic",
        help_text=(
            "Use only if assigning more than one portal topic, "
            "to control which topic is used as a breadcrumb."
        ),
    )
    portal_category = ParentalManyToManyField(PortalCategory, blank=True)

    notification = StreamField(
        [
            (
                "notification",
                molecules.Notification(),
            )
        ],
        blank=True,
        max_num=1,
        use_json_field=True,
    )

    content_panels = CFGOVPage.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("last_edited", heading="Last reviewed"),
                FieldPanel("question"),
                FieldPanel("statement"),
                FieldPanel("short_answer"),
            ],
            heading="Page content",
            classname="collapsible",
        ),
        FieldPanel("notification"),
        FieldPanel("answer_content"),
        MultiFieldPanel(
            [
                FieldPanel("related_resource"),
                AutocompletePanel(
                    "related_questions", target_model="ask_cfpb.AnswerPage"
                ),
            ],
            heading="Related resources and questions",
            classname="collapsible collapsed",
        ),
        MultiFieldPanel(
            [
                FieldPanel(
                    "portal_topic", widget=forms.CheckboxSelectMultiple
                ),
                FieldPanel("primary_portal_topic"),
                FieldPanel(
                    "portal_category", widget=forms.CheckboxSelectMultiple
                ),
            ],
            heading="Money Topic portal tags",
            classname="collapsible collapsed",
        ),
        MultiFieldPanel(
            [FieldPanel("featured")],
            heading="Featured answer on Ask landing page?",
            classname="collapsible collapsed",
        ),
    ]

    sidebar = StreamField(
        [
            ("call_to_action", molecules.CallToAction()),
            ("related_links", molecules.RelatedLinks()),
            ("related_metadata", molecules.RelatedMetadata()),
            (
                "email_signup",
                v1_blocks.EmailSignUpChooserBlock(),
            ),
            ("sidebar_contact", organisms.SidebarContactInfo()),
            ("rss_feed", molecules.RSSFeed()),
            ("social_media", molecules.SocialMedia()),
            (
                "reusable_text",
                v1_blocks.ReusableTextChooserBlock(ReusableText),
            ),
        ],
        blank=True,
        use_json_field=True,
    )

    sidebar_panels = [
        FieldPanel("sidebar"),
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading="Content"),
            ObjectList(sidebar_panels, heading="Sidebar"),
            ObjectList(CFGOVPage.settings_panels, heading="Configuration"),
        ]
    )

    template = "ask-cfpb/answer-page.html"

    def get_sibling_url(self):
        if self.answer_base:
            if self.language == "es":
                sibling = self.answer_base.english_page
            else:
                sibling = self.answer_base.spanish_page
            if sibling and sibling.live:
                return sibling.url

    def get_meta_description(self):
        """Determine what the page's meta and OpenGraph description should be

        Checks several different possible fields in order of preference.
        If none are found, returns an empty string, which is preferable to a
        generic description repeated on many pages.

        This method is overriding the standard one on CFGOVPage to factor in
        Ask CFPB AnswerPage-specific fields.
        """

        preference_order = [
            "search_description",
            "short_answer",
            "first_text",
        ]
        candidates = {}

        if self.search_description:
            candidates["search_description"] = self.search_description
        if self.short_answer:
            candidates["short_answer"] = strip_tags(self.short_answer)
        if hasattr(self, "answer_content"):
            for block in self.answer_content:
                if block.block_type == "text":
                    candidates["first_text"] = truncate_by_words_and_chars(
                        strip_tags(block.value["content"].source),
                        word_limit=35,
                        char_limit=160,
                    )
                    break

        for entry in preference_order:
            if candidates.get(entry):
                return candidates[entry]

        return ""

    def get_context(self, request, *args, **kwargs):
        # self.get_meta_description() is not called here because it is called
        # and added to the context by CFGOVPage's get_context() method.
        portal_topic = self.primary_portal_topic or self.portal_topic.first()
        context = super().get_context(request)
        context["related_questions"] = self.related_questions.all()
        context["last_edited"] = self.last_edited
        context["portal_page"] = get_portal_or_portal_search_page(
            portal_topic, language=self.language
        )
        context["breadcrumb_items"] = get_ask_breadcrumbs(
            language=self.language,
            portal_topic=portal_topic,
        )
        context["about_us"] = get_standard_text(self.language, "about_us")
        context["disclaimer"] = get_standard_text(self.language, "disclaimer")
        context["sibling_url"] = self.get_sibling_url()
        return context

    def answer_text(self):
        strings = []

        for fieldname in ("short_answer", "answer_content"):
            field = self._meta.get_field(fieldname)
            value = field.value_from_object(self)
            strings.extend(field.get_searchable_content(value))

        return "\n".join(filter(None, strings))

    def answer_content_preview(self):
        answer_text = self.answer_text()
        return truncate_by_words_and_chars(answer_text)

    def text(self):
        return "\n".join([self.question, self.answer_text()])

    def __str__(self):
        if self.answer_base:
            return f"{self.answer_base.id}: {self.title}"
        else:
            return self.title

    def validate_unique(self, *args, **kwargs):
        super().validate_unique(*args, **kwargs)

        if self.answer_base is None:
            return

        # Ensure that there is only ever one answer page in this language for
        # an answer
        pages_with_same_answer_and_language = self.__class__.objects.filter(
            language=self.language, answer_base=self.answer_base
        ).exclude(pk=self.pk)
        if pages_with_same_answer_and_language.exists():
            raise ValidationError(
                {
                    NON_FIELD_ERRORS: (
                        f"An answer page in {self.language} already exists "
                        f"for answer id {self.answer_base.id}"
                    )
                }
            )

    @property
    def clean_search_tags(self):
        return [tag.strip() for tag in self.search_tags.split(",")]

    # Returns an image for the page's meta Open Graph tag
    @property
    def meta_image(self):
        if self.social_sharing_image:
            return self.social_sharing_image

        if not self.category.exists():
            return None

        return self.category.first().category_image
