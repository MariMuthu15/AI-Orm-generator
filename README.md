1.Create a blazing virtual env:
    uv venv

2.Activate the env:
    source .venv/bin/activate

3.Install all the dependencies(UV way):
    uv add fastapi uvicorn[standard] pydantic python-dotenv openai httpx

4.If you have already poetry file:
    uv sync (or) uv sync --all-extras

5.Run the fast api:
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


API Call:
    Endpoint: http://localhost:8000/api/generate
    Method: POST
    Payload: {
  "query": "female engineering students in erode"
}
