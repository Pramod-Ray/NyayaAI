start cmd /k "cd Backend && uvicorn main:app --reload"
timeout /t 15
start cmd /k "streamlit run frontend/app.py"