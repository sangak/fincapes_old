import json
import pytz
from datetime  import timedelta
from django.conf import settings
from django.urls import reverse
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_save
from django.utils import timezone as tz
from django.utils.translation import gettext as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from thumbnails.fields import ImageField
from fincapes.utils import (
    unique_id_generator, unique_key_generator,
    get_date_time_local, get_due_date_time, saved_directory_path
)
from fincapes.variables import (
    LANGUAGE_CHOICES, USER_TYPE_CHOICES, USER_CATEGORY_CHOICES,
    GENDER_CHOICES
)

DEFAULT_ACTIVATION_DAYS = getattr(settings, 'DEFAULT_ACTIVATION_DAYS', 2)


def save_photo_avatar(instance, filename):
    return saved_directory_path(instance, filename, 'avatar')


class UserManager(BaseUserManager):
    def create_user(self, email, first_name=None, last_name=None, password=None,
                    is_active=True, is_staff=False, is_admin=False,
                    invited_user=False):
        user_obj = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            invited_user=invited_user
        )
        if password:
            user_obj.set_password(password)
        user_obj.staff = is_staff
        user_obj.admin = is_admin
        user_obj.is_active = is_active
        user_obj.save(using=self._db)
        return user_obj

    def create_staffuser(self, email, first_name=None, last_name=None, password=None,
                         invited_user=False):
        user = self.create_user(
            email, first_name=first_name, last_name=last_name, password=password, is_staff=True,
            invited_user=invited_user
        )
        return user

    def create_superuser(self, email, first_name=None, last_name=None, password=None,
                         invited_user=False):
        user = self.create_user(
            email, first_name=first_name, last_name=last_name, password=password, invited_user=invited_user,
            is_staff=True, is_admin=True
        )
        return user

    def save_profile(self, is_filled=None):
        profile = self.model(is_profile_filled=is_filled)
        profile.save(using=self._db)
        return profile


class User(AbstractBaseUser):
    email = models.EmailField(max_length=45, unique=True)
    uid = models.CharField(max_length=45, unique=True, editable=False)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_profile_filled = models.BooleanField(_('Profile Filled'), default=False)
    has_password_changed = models.BooleanField(default=False)
    invited_user = models.BooleanField(default=False)
    user_type = models.SmallIntegerField(default=1, choices=USER_TYPE_CHOICES)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = UserManager()

    def __str__(self):
        return str(self.email)

    @property
    def full_name(self):
        fname = self.first_name
        lname = self.last_name if self.last_name is not None else None
        return fname if lname is None else f"{fname} {lname}"

    def has_password(self):
        return True if self.password else False

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.staff

    @property
    def is_admin(self):
        return self.is_admin

    # def save_profile(self):
    #     self.objects.save_profile(True)
    #     self.is_profile_filled = True
    #     try:
    #         self.save()
    #     except ImportError:
    #         return False
    #     return True


class EmailActivationQueryset(models.query.QuerySet):
    def confirmable(self):
        now = tz.now()
        start_range = now - timedelta(days=DEFAULT_ACTIVATION_DAYS)
        end_range = now
        return self.filter(
            activated=False, force_expired=False
        ).filter(
            timestamp__gt=start_range, timestamp__lte=end_range
        )


class EmailActivationManager(models.Manager):
    def get_queryset(self):
        return EmailActivationQueryset(self.model, using=self._db)

    def confirmable(self):
        return self.get_queryset().confirmable()

    def email_exists(self, email):
        return self.get_queryset().filter(
            Q(email=email) | Q(user__email=email)
        ).filter(activated=False)


class EmailActivation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    key = models.CharField(max_length=120, blank=True, null=True)
    activated = models.BooleanField(default=False)
    force_expired = models.BooleanField(default=False)
    expires = models.SmallIntegerField(default=DEFAULT_ACTIVATION_DAYS)
    timestamp = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    objects = EmailActivationManager()

    def __str__(self):
        return str(self.email)

    def can_activate(self):
        qs = EmailActivation.objects.filter(pk=self.pk).confirmable()
        return True if qs.exists() else False

    def activate(self):
        if self.can_activate():
            user = self.user
            user.is_active = True
            user.save()
            self.activated = True
            self.save()
            return True
        return False

    def regenerate(self):
        self.key = None
        self.save()
        if self.key is not None:
            return True
        return False

    @property
    def get_due_date(self):
        local_date = get_date_time_local(self.timestamp, 'Asia/Jakarta')
        return get_due_date_time(local_date, self.expires)

    def send_activation(self):
        if not self.activated and not self.force_expired:
            if self.key:
                user_data = {
                    'from': settings.DEFAULT_FROM_EMAIL,
                    'key': self.key,
                    'email': self.email,
                    'expires': self.get_due_date
                }
                user_json = json.dumps(user_data)
                # send email activation
                return True
            return False


def pre_save_email_activation(sender, instance, *args, **kwargs):
    if not instance.activated and not instance.force_expired:
        if not instance.key:
            instance.key = unique_key_generator(instance)


pre_save.connect(pre_save_email_activation, sender=EmailActivation)


class ProfileQuerySet(models.query.QuerySet):
    def recent(self):
        return self.order_by('-updated')


class ProfileManager(models.Manager):
    def get_queryset(self):
        return ProfileQuerySet(self.model, using=self._db)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    uid = models.CharField(max_length=45, editable=False, unique=True)
    category = models.SmallIntegerField(default=3, choices=USER_CATEGORY_CHOICES)
    gender = models.SmallIntegerField(choices=GENDER_CHOICES, blank=True, null=True)
    no_tel = models.CharField(max_length=20, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    TIMEZONE_CHOICES = tuple(zip(pytz.all_timezones, pytz.all_timezones))
    timezone = models.CharField(max_length=32, default='Asia/Jakarta', choices=TIMEZONE_CHOICES, null=True, blank=True)
    language = models.CharField(
        default=settings.LANGUAGE_CODE, choices=LANGUAGE_CHOICES, max_length=3
    )
    photo = ImageField(pregenerated_sizes=['avatar', 'small'], upload_to=save_photo_avatar, null=True, blank=True)

    objects = ProfileManager()

    def __str__(self):
        return str(self.user.full_name)

    def get_absolute_url(self):
        return reverse('account:profile-detail', kwargs={'uid': self.uid})

    def profile_filled(self):
        user = self.user
        user.is_profile_filled = True
        user.save()

    def check_photo_is_available(self):
        if self.photo is not None:
            return True
        return False

    @property
    def split_tel(self):
        if self.no_tel is not None:
            tel = self.no_tel
            split = tel.split('-')
            code = split[0]
            phone = split[1]
            return code, phone
        return None, None

    def save_language(self, lang):
        self.language = lang
        try:
            self.save()
        except ImportError:
            return False
        return True


def pre_save_user_create(sender, instance, *args, **kwargs):
    if not instance.uid:
        instance.uid = unique_id_generator(instance)


pre_save.connect(pre_save_user_create, sender=User)


def post_save_user_create(instance, created, *args, **kwargs):
    if created:
        Profile.objects.create(user=instance)


post_save.connect(post_save_user_create, sender=User)


def pre_save_user_profile_create(sender, instance, *args, **kwargs):
    if not instance.uid:
        instance.uid = unique_id_generator(instance)


pre_save.connect(pre_save_user_profile_create, sender=Profile)