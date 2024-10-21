frontend:
	uv run streamlit run src/main_page.py

api:
	 uv run fastapi dev src/api/main_api.py
