from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django_quill.fields import QuillField
from thumbnails.fields import ImageField
from fincapes.helpers import get_date_human
from fincapes.utils import (
    unique_id_generator, unique_slug_generator,
    saved_directory_path
)

User = get_user_model()

STATUS_CHOICES = (
    (0, 'Draft'),
    (1, 'Publish')
)


def save_photo_path(instance, filename):
    return saved_directory_path(instance, filename, 'contents')


class ContentQuerySet(models.query.QuerySet):
    def recent(self):
        return self.order_by('-updated')
    
    def sliders(self):
        return self.filter(categories__contains='slider').order_by('-updated')
    
    
class ContentManager(models.Manager):
    def get_queryset(self):
        return ContentQuerySet(self.model, using=self._db)
    
    def get_by_pk(self, pk):
        qs = self.get_queryset().recent().filter(pk=pk)
        if qs.exists():
            return qs.first()
        return None
    
    def all(self):
        return self.get_queryset().recent().all()
        
    def get_sliders(self):
        qs = self.get_queryset().sliders()
        if qs.exists():
            return qs
        return None
    
    
class Content(models.Model):
    uid = models.CharField(max_length=64, unique=True, editable=False)
    title = models.CharField(max_length=300, blank=True, null=True)
    title_animation = models.CharField(max_length=300, blank=True, null=True)
    title_id = models.CharField(max_length=400, blank=True, null=True, help_text='Title article in Bahasa Indonesia')
    title_id_animation = models.CharField(max_length=400, blank=True, null=True)
    slug = models.SlugField(max_length=500, unique=True, editable=False)
    slug_id = models.SlugField(max_length=550, editable=False)
    photo = ImageField(pregenerated_sizes=['small', 'medium'], upload_to=save_photo_path, null=True, blank=True)
    photo_caption = models.CharField(max_length=200, null=True, blank=True)
    photo_caption_id = models.CharField(max_length=250, null=True, blank=True)
    brief_description = models.CharField(max_length=400, blank=True, null=True)
    brief_description_id = models.CharField(max_length=500, blank=True, null=True)
    article = QuillField(null=True)
    article_id = QuillField(null=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0)
    categories = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='added_article', null=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='modified_article', null=True)

    objects = ContentManager()
    
    def __str__(self):
        return self.title if self.title is not None else self.title_id
    
    def get_absolute_url(self):
        return reverse("article:detail", kwargs={"pk": self.pk, 'slug': self.slug})
    
    @property
    def get_update(self):
        tgl = str(self.timestamp)
        return get_date_human(tgl)
    

def pre_save_content_create(instance, *args, **kwargs):
    if not instance.uid:
        instance.uid = unique_id_generator(instance)
        
    if instance.title:
        instance.slug = slugify(instance.title)
    if instance.title_id:
        instance.slug_id = slugify(instance.title_id)
        

pre_save.connect(pre_save_content_create, sender=Content)    