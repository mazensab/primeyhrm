# ============================================================
# 🇸🇦 National Address Cache Service
# Primey HR Cloud | Settings Center
# ============================================================

from settings_center.models import (
    NationalAddressCity,
    NationalAddressDistrict,
    NationalAddressStreet,
)


def cache_address(city_name=None, district_name=None, street_name=None):
    """
    🧠 Cache Saudi National Address components safely
    - City
    - District
    - Street
    """

    if not city_name:
        return

    city, _ = NationalAddressCity.objects.get_or_create(
        name=city_name.strip()
    )

    if district_name:
        district, _ = NationalAddressDistrict.objects.get_or_create(
            name=district_name.strip(),
            city=city,
        )
    else:
        district = None

    if street_name and district:
        NationalAddressStreet.objects.get_or_create(
            name=street_name.strip(),
            district=district,
        )
