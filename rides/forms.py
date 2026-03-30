from django import forms

_CONTROL = (
    "w-full rounded-xl border border-white/30 bg-white/50 px-4 py-3 "
    "text-slate-900 outline-none transition focus:ring-2 focus:ring-violet-500/40 "
    "dark:border-slate-600 dark:bg-slate-900/50 dark:text-white placeholder:text-slate-400"
)


class BookRideForm(forms.Form):
    pickup_location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Pickup address or landmark"}),
    )
    drop_location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Drop-off address or landmark"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = _CONTROL
