from django import forms

class UploadXMLForm(forms.Form):
    xml_file = forms.FileField(
        label="Choose XML file",
        help_text="Upload PubMed XML (.xml) flie."
    )

    def clean_xml_file(self):
        file = self.cleaned_data.get("xml_file")
        if file:
            # 檢查副檔名
            if not file.name.endswith(".xml"):
                raise forms.ValidationError("只允許上傳 .xml 檔案")

        return file