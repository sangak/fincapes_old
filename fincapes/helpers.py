import logging
import pendulum
from ajax_datatable.views import AjaxDatatableView
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import get_language
from crispy_forms.layout import BaseInput, Field
from crispy_forms.utils import get_template_pack
from django import forms

logger = logging.getLogger(__name__)


class Submit(BaseInput):
    input_type = 'submit'
    
    def __init__(self, *args, **kwargs):
        self.field_classes = 'submit submit-button' if get_template_pack() == 'uni_form' else 'btn'
        super().__init__(*args, **kwargs)
        

class PercentageField(forms.FloatField):
    widget = forms.TextInput(
        attrs={
            'class': 'percent-input'
        }
    )
    
    def to_python(self, value):
        val = super().to_python(value)
        if is_number(val):
            return val/100
        return val
    
    def prepare_value(self, value):
        val = super().prepare_value(value)
        if is_number(val) and not isinstance(val, str):
            return str(float(val) * 100)
        return val
    

class DatatableView(AjaxDatatableView):
    def get_table_row_id(self, request, obj):
        result = ''
        if self.table_row_id_fieldname:
            try:
                result = str(getattr(obj, self.table_row_id_fieldname))
            except:
                result = ''
        return result
        

def is_number(s):
    if s is None:
        return False
    try:
        float(s)
        return True
    except KeyError:
        return False
    
    
def email_validator(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False
    
    
def check_date_valid(s):
    date_list = s.split('/')
    try:
        year = date_list[2]
        month = date_list[1]
        day = date_list[0]
        
        new_date = pendulum.date(
            int(year), int(month), int(day)
        )
        correct_date = True
        return correct_date, new_date
    except ValueError:
        new_date = None
        correct_date = False
        return correct_date, new_date
    

def split_name(fullname):
    fname_split = fullname.split(" ")
    lname = None
    fname = None
    for num, name in enumerate(fname_split):
        if num == 0:
            fname = name
        else:
            if lname is None:
                lname = name
            else:
                lname += " " + name
    return fname, lname


def remove_session(request, session_name):
    try:
        del request.session[session_name]
    except KeyError:
        pass


def get_current_full_date(location='Asia/Jakarta'):
    dt = pendulum.today(tz=location)
    bhs = get_language()
    pattern = 'DD MMMM YYYY' if bhs == 'id' else 'MMMM DD, YYYY'
    return dt.format(pattern, locale=bhs)


def get_locale_full_date(date_model, day_name_include=False):
    year = date_model.year
    month = date_model.month
    day = date_model.day
    tgl = pendulum.date(year, month, day)
    bhs = get_language()
    pattern = 'dddd DD MMMM YYYY' if day_name_include else 'DD MMMM YYYY'
    return tgl.format(pattern, locale=bhs)


def get_locale_date(tgl, bhs=None):
    try:
        bhs = get_language() if bhs is None else bhs
        pattern = 'DD/MM/YYYY' if bhs == 'id' else 'MM/DD/YYYY'
        year = tgl.year
        month = tgl.month
        day = tgl.day
        dt = pendulum.date(year, month, day)
        return dt.format(pattern)
    except:
        tgl_ = pendulum.today(tz='Asia/Jakarta')
        return tgl_.format('DD/MM/YYYY')


def get_date_human(tanggal):
    try:
        bahasa = get_language()
        dt = pendulum.parse(tanggal)
        return dt.diff_for_humans(locale=bahasa)
    except:
        return False