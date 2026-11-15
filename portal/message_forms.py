from django import forms


class NewConversationForm(forms.Form):
    subject = forms.CharField(max_length=160, strip=True)
    body = forms.CharField(max_length=5000, strip=True, widget=forms.Textarea(attrs={"rows": 6}))

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Please enter your message.")
        return body


class ReplyForm(forms.Form):
    body = forms.CharField(
        max_length=5000, strip=True,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Write a reply…"}),
    )
