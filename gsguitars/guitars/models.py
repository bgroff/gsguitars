from django.db import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.management import call_command
from django.dispatch import receiver
from django.shortcuts import render
from django.http import HttpResponse

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, \
    InlinePanel, PageChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.models import Image
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.snippets.models import register_snippet

from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager
from taggit.models import Tag, TaggedItemBase

COMMON_PANELS = (
    FieldPanel('slug'),
    FieldPanel('seo_title'),
    FieldPanel('show_in_menus'),
    FieldPanel('search_description'),
)


# A couple of abstract classes that contain commonly used fields

class LinkFields(models.Model):
    link_external = models.URLField("External link", blank=True)
    link_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.CASCADE
    )
    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.CASCADE
    )

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        else:
            return self.link_external

    panels = [
        FieldPanel('link_external'),
        PageChooserPanel('link_page'),
        DocumentChooserPanel('link_document'),
    ]

    class Meta:
        abstract = True


class ContactFields(models.Model):
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address_1 = models.CharField(max_length=255, blank=True)
    address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    post_code = models.CharField(max_length=10, blank=True)

    panels = [
        FieldPanel('telephone'),
        FieldPanel('email'),
        FieldPanel('address_1'),
        FieldPanel('address_2'),
        FieldPanel('city'),
        FieldPanel('country'),
        FieldPanel('post_code'),
    ]

    class Meta:
        abstract = True


# Carousel items

class CarouselItem(LinkFields):
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    embed_url = models.URLField("Embed URL", blank=True)
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('embed_url'),
        FieldPanel('caption'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Related links

class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        FieldPanel('title'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True

# Home Page

class HomePageCarouselItem(Orderable, CarouselItem):
    page = ParentalKey('guitars.HomePage', related_name='carousel_items')


class HomePageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('guitars.HomePage', related_name='related_links')


class HomePage(Page):
    body = RichTextField(blank=True)

    indexed_fields = ('body', )
    search_name = "Homepage"
    subpage_types = []

    class Meta:
        verbose_name = "Homepage"

HomePage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    InlinePanel('carousel_items', label="Carousel items"),
    InlinePanel('related_links', label="Related links"),
]

HomePage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]



# Contact page

class ContactPage(Page, ContactFields):
    body = RichTextField(blank=True)
    feed_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    subpage_types = []

    indexed_fields = ('body', )
    search_name = "Contact information"

ContactPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    MultiFieldPanel(ContactFields.panels, "Contact"),
]

ContactPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
    ImageChooserPanel('feed_image'),
]


# Blog index page

class GuitarIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('guitars.GuitarIndexPage', related_name='related_links')


class GuitarIndexPage(Page):
    intro = RichTextField(blank=True)

    indexed_fields = ('intro', )
    search_name = "Guitar"
    subpage_types = ['GuitarPage']

    @property
    def guitars(self):
        # Get list of blog pages that are descendants of this page
        guitars = GuitarPage.objects.filter(
            live=True,
            path__startswith=self.path
        )

        # Order by most recent date first
        guitars = guitars.order_by('-date')

        return guitars

    def tags(self):
        return Tag.objects.filter(id__in=self.guitars.all().values_list('carousel_items__image__tags', flat=True)).distinct()

    def serve(self, request):
        # Get guitars
        guitars = self.guitars

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            guitars = guitars.filter(tags__name=tag)

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(guitars, 10)  # Show 10 blogs per page
        try:
            guitars = paginator.page(page)
        except PageNotAnInteger:
            guitars = paginator.page(1)
        except EmptyPage:
            guitars = paginator.page(paginator.num_pages)

        return render(request, self.template, {
            'self': self,
            'guitars': guitars,
        })

GuitarIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('related_links', label="Related links"),
]

GuitarIndexPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]


# Blog page

class GuitarPageCarouselItem(Orderable, CarouselItem):
    page = ParentalKey('guitars.GuitarPage', related_name='carousel_items')


class GuitarPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('guitars.GuitarPage', related_name='related_links')


class GuitarPageTag(TaggedItemBase):
    content_object = ParentalKey('guitars.GuitarPage', related_name='tagged_items')


class GuitarPage(Page):
    body = RichTextField()
    tags = ClusterTaggableManager(through=GuitarPageTag, blank=True)
    date = models.DateField("Post date")
    msrp = models.DecimalField(max_digits=10, decimal_places=2)
    feed_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    indexed_fields = ('body', )
    search_name = "Guitar"
    subpage_types = []

    def get_tags(self):
        return Tag.objects.filter(id__in=self.carousel_items.values_list('image__tags', flat=True)).distinct()

    @property
    def guitar_index(self):
        # Find blog index in ancestors
        for ancestor in reversed(self.get_ancestors()):
            if isinstance(ancestor.specific, GuitarIndexPage):
                return ancestor

        # No ancestors are blog indexes,
        # just return first blog index in database
        return GuitarIndexPage.objects.first()

GuitarPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('date'),
    FieldPanel('body', classname="full"),
    FieldPanel('msrp'),
    InlinePanel('carousel_items', label="Carousel items"),
    InlinePanel('related_links', label="Related links"),
]

GuitarPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
    ImageChooserPanel('feed_image'),
    FieldPanel('tags'),
]
