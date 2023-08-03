import datetime
import os
import pytz
import random
import re
import string
from dateutil import parser
from django.utils.text import slugify
from django.db.models import Q


def get_date_time_local(date_model, tzinfo="Asia/Jakarta"):
    zone = pytz.timezone(tzinfo)
    localtime = date_model.astimezone(zone)
    return localtime


def last_time_today(date_model, tzinfo="Asia/Jakarta"):
    date_ = get_date_time_local(date_model, tzinfo)
    today = date_.date()
    last_time = datetime.datetime.max.time()
    return datetime.datetime.combine(today, last_time)


def convert_string_to_datetime(date_string):
    date_ = parser.parser(date_string)
    return date_


def get_time_diff(instance):
    start = instance.date_start
    end = instance.date_end
    timediff = end - start
    return timediff.days


def get_due_date_time(date_model, skip, include_time=True):
    due_date = date_model + datetime.timedelta(days=skip)
    date_format = "%d-%m-%Y %H:%M:%S" if include_time else "%d-%m-%Y"
    return due_date.strftime(date_format)


def get_last_month_date(date_model):
    this_month_start = datetime.datetime(date_model.year, date_model.month, 1)
    last_month_end = this_month_start - datetime.timedelta(days=1)
    last_month_start = datetime.datetime(last_month_end.year, last_month_end.month, 1)
    return last_month_start, last_month_end


def get_month_data_range(months_ago=1, include_this_month=False):
    today = datetime.datetime.now().today()
    dates_ = []
    if include_this_month:
        next_month = today.replace(day=28) + datetime.timedelta(days=4)
        start, end = get_last_month_date(next_month)
        dates_.insert(0, {
            "start": start.timestamp(),
            "end": end.timestamp(),
            "start_json": start.isoformat(),
            "end_json": end.isoformat(),
            "timesince": 0,
            "year": start.year,
            "month": str(start.strftime("%B")),
        })
    for x in range(0, months_ago):
        start, end = get_last_month_date(today)
        today = start
        dates_.insert(0, {
            "start": start.timestamp(),
            "end": end.timestamp(),
            "start_json": start.isoformat(),
            "timesince": int((datetime.datetime.now() - end).total_seconds()),
            "year": start.year,
            "month": str(start.strftime("%B")),
        })
    return dates_


def get_filename(path):
    return os.path.basename(path)


def get_filename_ext(filepath):
    basename = get_filename(filepath)
    name, ext = os.path.splitext(basename)
    return name, ext


def saved_directory_path(instance, filename, root):
    size = random.randint(3, 5)
    uid = instance.uid
    name, ext = get_filename_ext(filename)
    new_str = random_string_generator(size=size)
    new_filename = "{}{}".format(uid, new_str)
    final_filename = "{}/{}{}".format(root, new_filename, ext)
    return final_filename


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_password(size=8):
    chars = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$_'
    password = random_string_generator(size=size, chars=chars)
    return password


def unique_key_generator(instance):
    size = random.randint(30, 45)
    key = random.randint(30, 45)
    Klass = instance.__class__
    qs_exists = Klass.objects.filter(key=key).exists()
    if qs_exists:
        return unique_key_generator(instance)
    return key


def unique_slug_generator(instance, new_slug=None):
    if new_slug is not None:
        slug = new_slug
    else:
        if instance.title:
            slug = slugify(instance.title)
        else:
            slug = random_string_generator(size=20)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(slug=slug).filter(
        ~Q(slug=instance.slug)
    ).exists()

    if qs_exists:
        new_slug = "{}-{}".format(
            slug, random_string_generator(size=6)
        )
        return unique_slug_generator(instance, new_slug=new_slug)

    return slug


def unique_id_generator(instance):
    size = random.randint(40, 45)
    new_id = random_string_generator(size=size)
    Klass = instance.__class__
    qs_exists = Klass.objects.filter(uid=new_id).exists()
    if qs_exists:
        return unique_slug_generator(instance)
    return new_id


def currency(amount, lang='id'):
    cur = round(int(amount))
    separator = ',' if lang == 'id' else '.'
    separator_ = '.' if lang == 'id' else ','
    dec = ',-' if lang == 'id' else '.-'
    return '{:,}'.format(cur).replace(separator, separator_) + dec


def year_list(years=5):
    current_year = datetime.datetime.today().year
    list_of_year = [current_year - i for i in range(years)]
    keys = [str(x) for x in list_of_year]
    return tuple(zip(keys, keys))


def string_separator_to_number(string_number):
    pattern = r"\,|\.|(?=\d{3})\,|\.|-"
    angka = re.sub(pattern, "", string_number)
    return int(angka)