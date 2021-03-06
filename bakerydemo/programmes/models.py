from datetime import datetime

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel, StreamFieldPanel
from wagtail.wagtailcore.models import Orderable, Page
from wagtail.wagtailsearch import index
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel

from bakerydemo.base.blocks import BaseStreamBlock
from bakerydemo.programmes.choices import DAY_CHOICES


class OperatingHours(models.Model):
    """
    A Django model to capture operating hours for a Location
    """

    day = models.CharField(
        max_length=4,
        choices=DAY_CHOICES,
        default='MON'
    )
    opening_time = models.TimeField(
        blank=True,
        null=True
    )
    closing_time = models.TimeField(
        blank=True,
        null=True
    )
    closed = models.BooleanField(
        "Closed?",
        blank=True,
        help_text='Tick if location is closed on this day'
    )

    panels = [
        FieldPanel('day'),
        FieldPanel('opening_time'),
        FieldPanel('closing_time'),
        FieldPanel('closed'),
    ]

    class Meta:
        abstract = True

    def __str__(self):
        if self.opening_time:
            opening = self.opening_time.strftime('%H:%M')
        else:
            opening = '--'
        if self.closing_time:
            closed = self.opening_time.strftime('%H:%M')
        else:
            closed = '--'
        return '{}: {} - {} {}'.format(
            self.day,
            opening,
            closed,
            settings.TIME_ZONE
        )


class ProgrammeOperatingHours(Orderable, OperatingHours):
    """
    A model creating a relationship between the OperatingHours and Location
    Note that unlike BlogPeopleRelationship we don't include a ForeignKey to
    OperatingHours as we don't need that relationship (e.g. any Location open
    a certain day of the week). The ParentalKey is the minimum required to
    relate the two objects to one another. We use the ParentalKey's related_
    name to access it from the LocationPage admin
    """
    location = ParentalKey(
        'ProgrammePage',
        related_name='hours_of_operation'
    )


class ProgrammesIndexPage(Page):
    """
    A Page model that creates an index page (a listview)
    """
    introduction = models.TextField(
        help_text='Text to describe the page',
        blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Landscape mode only; horizontal width between 1000px and 3000px.'
    )

    # Only LocationPage objects can be added underneath this index page
    subpage_types = ['ProgrammePage']

    # Allows children of this indexpage to be accessible via the indexpage
    # object on templates. We use this on the homepage to show featured
    # sections of the site and their child pages
    def children(self):
        return self.get_children().specific().live()

    # Overrides the context to list all child
    # items, that are live, by the date that they were published
    # http://docs.wagtail.io/en/latest/getting_started/tutorial.html#overriding-context
    def get_context(self, request):
        context = super(ProgrammesIndexPage, self).get_context(request)
        context['locations'] = ProgrammePage.objects.descendant_of(
            self).live().order_by(
            'title')
        return context

    content_panels = Page.content_panels + [
        FieldPanel('introduction', classname="full"),
        ImageChooserPanel('image'),
    ]


class ProgrammePage(Page):
    """
    Detail for a specific bakery location.
    """
    introduction = models.TextField(
        help_text='Text to describe the page',
        blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Landscape mode only; horizontal width between 1000px and 3000px.'
    )
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )
   

    # Search index configuration
    search_fields = Page.search_fields + [
       
        index.SearchField('body'),
    ]

    # Fields to show to the editor in the admin view
    content_panels = [
        FieldPanel('title', classname="full"),
        FieldPanel('introduction', classname="full"),
        ImageChooserPanel('image'),
        StreamFieldPanel('body'),
     
    ]

    def __str__(self):
        return self.title

  

    # Makes additional context available to the template so that we can access
    # the latitude, longitude and map API key to render the map
    def get_context(self, request):
        context = super(ProgrammePage, self).get_context(request)
      
        return context

    # Can only be placed under a LocationsIndexPage object
    parent_page_types = ['ProgrammesIndexPage']
