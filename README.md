# GST JANO

Independent GST information app for India (English and Hindi). Search goods by name, HSN code or rate, view tax class and split, calculate GST, compare old and new rates, and read GST payment guidance.

GST JANO is not a Government of India, CBIC, GSTN or GST Council application. Information is general and is not tax or legal advice.

## Files
- `app.py` : the Streamlit app
- `gst_data.csv` : GST data table (the sample rows are TEST ONLY; replace with verified CBIC data)
- `requirements.txt` : Python libraries

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Upload these files to a public GitHub repository (all at the top level), then deploy at share.streamlit.io with main file `app.py`.

## Data rules
Add a row to `gst_data.csv` only with a rate copied from an official CBIC notification. Fill `source_url` and `last_checked`. Set `verified` to YES only after checking.
