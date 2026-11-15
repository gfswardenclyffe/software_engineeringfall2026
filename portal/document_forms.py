from pathlib import Path
from django import forms
from .models import ClientDocument

MAX_DOCUMENT_SIZE = 10 * 1024 * 1024

class ClientDocumentForm(forms.ModelForm):
    class Meta:
        model = ClientDocument
        fields = ("title", "file")

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if uploaded.size > MAX_DOCUMENT_SIZE:
            raise forms.ValidationError("The maximum document size is 10 MB.")
        if Path(uploaded.name).suffix.lower() != ".pdf":
            raise forms.ValidationError("Only PDF documents are supported.")
        prefix = uploaded.read(5)
        uploaded.seek(0)
        if prefix != b"%PDF-":
            raise forms.ValidationError("This file is not a valid PDF.")
        return uploaded
