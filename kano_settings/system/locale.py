#
# locale.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Set configuration for i18n locale
#
# Note: Several conflicting conventions are used by the system tools for the
# naming of locales. Here, everything will be converted to use UTF-8 and take
# the standard format
#
#     <language>_<REGION>.UTF-8
#


import re
import os

from kano.utils import run_cmd, read_file_contents, sed, enforce_root, \
    read_file_contents_as_lines, get_user_unsudoed, get_home_by_username, \
    chown_path
import kano_settings.system.keyboard_layouts as keyboard_layouts

SUPPORTED_LIST_FILE = '/usr/share/i18n/SUPPORTED'
LOCALE_GEN_FILE = '/etc/locale.gen'
LOCALE_PARAMS = [
    # 'LANG',  # Determines the default locale in the absence of other locale related environment variables
    'LANGUAGE',  #
    'LC_ADDRESS',  # Convention used for formatting of street or postal addresses
    'LC_COLLATE',  # Collation order
    'LC_CTYPE',  # Character classification and case conversion
    'LC_MONETARY',  # Monetary formatting
    'LC_MEASUREMENT',  # Default measurement system used within the region
    'LC_MESSAGES',  # Format of interactive words and responses
    'LC_NUMERIC',  # Numeric formatting
    'LC_PAPER',  # Default paper size for region
    'LC_RESPONSE',  # Determines how responses (such as Yes and No) appear in the local language
    'LC_TELEPHONE',  # Conventions used for representation of telephone numbers
    'LC_TIME'  # Date and time formats
]


def is_locale_valid(locale):
    """
    The supported file list (UTF-8) entries take the form
        <language>_<REGION>[.\s]UTF-8(\sUTF-8)?
    """

    return re.search(standard_locale_to_genfile_entry(locale),
                     read_file_contents(SUPPORTED_LIST_FILE))


def is_locale_installed(locale):
    """
    The `locale --all-locales` command returns entries of the form
        <language>_<REGION>.utf8
    """

    locale = ensure_utf_locale(locale)

    locales, dummy, dummy = run_cmd('locale --all-locales')
    locales = [ensure_utf_locale(l) for l in locales.splitlines()]

    return locale in locales


def ensure_utf_locale(locale):
    return re.sub(r'^([a-z]{2}_[A-Z]{2})(?:\.|$).*', r'\1.UTF-8', locale)


def strip_encoding_from_locale(locale):
    return locale.split('.')[0]


def split_locale(locale):
    locale = strip_encoding_from_locale(locale)

    return locale.split('_')


def standard_locale_to_genfile_entry(locale):
    '''
    The locale gen file (UTF-8) entries take the form
        <language>_<REGION>[.\s]UTF-8(\sUTF-8)?
    '''

    locale = ensure_utf_locale(locale)
    locale_code = locale.split('.')[0]

    return locale_code + r'[\.\s]UTF-8(\sUTF-8)?'


def install_locale(locale):
    locale = ensure_utf_locale(locale)

    if not is_locale_valid(locale):
        print 'locale not valid', locale
        return False

    enforce_root(_('You need to be root to change install a locale'))

    genfile_locale = standard_locale_to_genfile_entry(locale)
    sed(r'^# ({})'.format(genfile_locale), r'\1', LOCALE_GEN_FILE)
    run_cmd('locale-gen')


def uninstall_locale(locale):
    locale = ensure_utf_locale(locale)

    if not is_locale_valid(locale):
        print 'locale not valid'
        return False

    enforce_root(_('You need to be root to change install a locale'))

    genfile_locale = standard_locale_to_genfile_entry(locale)
    sed('^({})'.format(genfile_locale), r'# \1', LOCALE_GEN_FILE)
    run_cmd('locale-gen')


def set_locale_param(param, locale, skip_check=False):
    # FIXME: Don't use the .xsessionrc file to set the locale
    XSESSION_RC_FILE = os.path.join(get_home_by_username(get_user_unsudoed()),
                                    '.xsessionrc')
    if not skip_check and not is_locale_installed(locale):
        install_locale(locale)

    param_found = False
    new_param_line = 'export {}={}'.format(param, locale)
    new_config_file = []

    if os.path.exists(XSESSION_RC_FILE):
        xsession_file = read_file_contents_as_lines(XSESSION_RC_FILE)

        for line in xsession_file:
            if param in line:
                line = new_param_line
                param_found = True

            new_config_file.append(line)

    if not param_found:
        new_config_file.append(new_param_line)

    with open(XSESSION_RC_FILE, 'w') as conf_file:
        conf_file.write('\n'.join(new_config_file))

    chown_path(XSESSION_RC_FILE)


def set_locale(locale):
    locale = ensure_utf_locale(locale)

    if not is_locale_installed(locale):
        install_locale(locale)

    for param in LOCALE_PARAMS:
        set_locale_param(param, locale, skip_check=True)


def get_locale():
    return os.environ['LANG']


def country_code_to_layout_keys(country_code):
    import pycountry  # lazy import since it takes a long time

    try:
        country = pycountry.countries.get(alpha2=country_code.upper())
        country_name = country.name
    except KeyError:
        country_name = 'United States'

    for continent, countries in keyboard_layouts.layouts.iteritems():
        for candidate_country in countries.iterkeys():
            if country_name == candidate_country:
                return continent, country_name

    return 'america', 'United States'


def locale_to_layout_keys(locale):
    dummy_lang, country_code = split_locale(locale)
    return country_code_to_layout_keys(country_code)


def layout_keys_to_indexes(continent_key, country_key):
    continent_list = [
        continent.lower() for continent in keyboard_layouts.get_continents()
    ]
    country_list = keyboard_layouts.sorted_countries(
        keyboard_layouts.get_countries_for_continent(continent_key)
    )

    try:
        continent_idx = continent_list.index(continent_key)
    except ValueError:
        continent_idx = 1  # America's index

    try:
        country_idx = country_list.index(country_key)
    except ValueError:
        country_idx = 21  # US country index

    return continent_idx, country_idx
