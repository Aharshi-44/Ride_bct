from django import forms

_CONTROL = "form-control"


class BookRideForm(forms.Form):
    pickup_location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Pickup address or landmark"}),
    )
    drop_location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Drop-off address or landmark"}),
    )
    pickup_lat = forms.CharField(required=False, widget=forms.HiddenInput())
    pickup_lng = forms.CharField(required=False, widget=forms.HiddenInput())
    drop_lat = forms.CharField(required=False, widget=forms.HiddenInput())
    drop_lng = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = _CONTROL

        for name in ("pickup_lat", "pickup_lng", "drop_lat", "drop_lng"):
            self.fields[name].widget.attrs.pop("class", None)

    def clean(self):
        cleaned = super().clean()
        pickup_txt = (cleaned.get("pickup_location") or "").strip()
        drop_txt = (cleaned.get("drop_location") or "").strip()
        plat = (cleaned.get("pickup_lat") or "").strip()
        plng = (cleaned.get("pickup_lng") or "").strip()
        dlat = (cleaned.get("drop_lat") or "").strip()
        dlng = (cleaned.get("drop_lng") or "").strip()

        if pickup_txt and (not plat or not plng):
            self.add_error("pickup_location", "Please select a pickup location from the suggestions.")
        if drop_txt and (not dlat or not dlng):
            self.add_error("drop_location", "Please select a drop-off location from the suggestions.")

        cleaned["pickup_lat"] = plat
        cleaned["pickup_lng"] = plng
        cleaned["drop_lat"] = dlat
        cleaned["drop_lng"] = dlng
        cleaned["pickup_location"] = pickup_txt
        cleaned["drop_location"] = drop_txt
        return cleaned
